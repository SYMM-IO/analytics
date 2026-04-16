import { Component, Input, OnInit } from "@angular/core"
import { EnvironmentService } from "../services/enviroment.service"
import { GraphQlClient, QueryConfig } from "../services/graphql-client"
import { EnvironmentInterface, Solver } from "../../environments/environment-interface"
import { LoadingService } from "../services/Loading.service"
import { TuiAlertService } from "@taiga-ui/core"
import { BaseHistory, SolverDailyHistory } from "../models"
import { BehaviorSubject, catchError, combineLatest, map, Observable, of, shareReplay, tap, zip } from "rxjs"
import { GroupedHistory } from "../groupedHistory"
import BigNumber from "bignumber.js"
import { aggregateSolverDailyHistories } from "../utils/aggregate-utils"
import { aggregateHistories, collectAllDates, justifyHistoriesToDates } from "../utils/common-utils"

type SolverHistoryResult = {
	environmentName: string
	solver: Solver
	dailyHistories: SolverDailyHistory[]
}

@Component({
    selector: "app-solvers-charts",
    templateUrl: "./solvers-charts.component.html",
    styleUrls: ["./solvers-charts.component.scss"],
    standalone: false
})
export class SolversChartsComponent implements OnInit {
	groupedHistories?: Observable<GroupedHistory[]>
	@Input() set selectedChainNames(value: string[] | null | undefined) {
		this.selectedChainNames$.next(value ? [...value] : [])
	}
	environments: EnvironmentInterface[]
	private readonly selectedChainNames$ = new BehaviorSubject<string[]>([])

	constructor(
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		protected readonly alert: TuiAlertService,
	) {
		this.environments = environmentService.getValue("environments")
	}

	ngOnInit(): void {
		const environmentResults$ = zip(
			this.environments.map((env: EnvironmentInterface) => {
				const graphQlClient = new GraphQlClient(env.subgraphUrl!, this.loadingService)

				const configSets = env.solvers!.map(solver => ({
					configs: [
						{
							method: "solverDailyHistories",
							fields: [
								"id",
								"tradeVolume",
								"averagePositionSize",
								"positionsCount",
								"fundingPaid",
								"fundingReceived",
								"openInterest",
								"accountSource",
								"solver",
								"timestamp",
							],
							first: 1000,
							orderBy: "timestamp",
							conditions: [
								{
									field: "solver",
									operator: "contains",
									value: `"${solver.address!.toLowerCase()}"`,
								},
								{
									field: "tradeVolume",
									operator: "gt",
									value: `"0"`,
								},
							],
							createFunction: (obj: any) => SolverDailyHistory.fromRawObject(obj).applyDecimals(env.collateralDecimal!),
						},
					] as QueryConfig<any>[],
				}))

				return this.loadEnvironmentResults(
					env,
					graphQlClient.batchLoadAll(configSets, 1000).pipe(
						map(results =>
							results.map((result, index) => ({
								environmentName: env.name,
								solver: env.solvers![index],
								dailyHistories: (result["solverDailyHistories"] || []) as SolverDailyHistory[],
							})),
						),
					),
					() =>
						env.solvers!.map(solver => ({
							environmentName: env.name,
							solver,
							dailyHistories: [] as SolverDailyHistory[],
						})),
				)
			}),
		).pipe(
			map(envResults => envResults.flat()),
			catchError(err => {
				this.loadingService.setLoading(false)
				this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
				throw err
			}),
			shareReplay(1),
		)

		this.groupedHistories = combineLatest([environmentResults$, this.selectedChainNames$]).pipe(
			map(([environmentResults, selectedChainNames]) => {
				const selectedChainsSet = new Set(selectedChainNames)
				const filteredResults = environmentResults.filter(result => selectedChainsSet.has(result.environmentName))
				const out: GroupedHistory[] = []

				for (let i = 0; i < filteredResults.length; i++) {
					const result = filteredResults[i]
					result.solver.id = i
					if (result.dailyHistories.length > 0)
						out.push({
							index: result.solver,
							dailyHistories: result.dailyHistories,
							weeklyHistories: [],
							monthlyHistories: [],
						})
				}

				const all_dates = collectAllDates(out, "dailyHistories")
				out.forEach(groupedHistory => {
					let mapped_data = new Map<number, SolverDailyHistory>()
					for (const history of groupedHistory.dailyHistories) {
						const time = BaseHistory.getTime(history)!
						if (mapped_data.has(time)) {
							let lastHistory = mapped_data.get(time)!
							let aggregatedHistory = aggregateSolverDailyHistories([lastHistory, history])
							aggregatedHistory.timestamp = lastHistory.timestamp! >= history.timestamp! ? lastHistory.timestamp : history.timestamp
							mapped_data.set(time, aggregatedHistory)
						} else {
							mapped_data.set(time, history)
						}
					}
					groupedHistory.dailyHistories = justifyHistoriesToDates([...mapped_data.values()], all_dates)
				})

				const map = new Map<string, GroupedHistory>()
				for (const groupedHistory of out) {
					const key = groupedHistory.index.name!
					if (map.has(key)) {
						let existingHistory = map.get(key)!
						existingHistory.dailyHistories = aggregateHistories(
							groupedHistory.dailyHistories,
							existingHistory.dailyHistories,
							aggregateSolverDailyHistories,
						)
						map.set(key, existingHistory)
					} else {
						map.set(key, groupedHistory)
					}
				}
				return [...map.values()]
			}),
			shareReplay(1),
		)
	}

	private loadEnvironmentResults<T>(env: EnvironmentInterface, source$: Observable<T>, fallbackFactory: () => T): Observable<T> {
		return source$.pipe(
			tap(() => this.environmentService.markSubgraphLoaded(env.name)),
			catchError(error => {
				this.notifyIgnoredEnvironment(env, error)
				return of(fallbackFactory())
			}),
		)
	}

	private notifyIgnoredEnvironment(env: EnvironmentInterface, error: unknown) {
		if (!this.environmentService.markSubgraphIgnored(env.name)) return

		const message =
			error instanceof Error && error.message.includes("timed out")
				? `${env.name} is ignored because its subgraph did not respond within ${GraphQlClient.REQUEST_TIMEOUT_MS / 1000}s.`
				: `${env.name} is ignored because its subgraph is unavailable.`

		this.alert.open(message).subscribe()
	}

	moneyValueFormatter(x: any) {
		return BigNumber(x).toFormat(3)
	}
}
