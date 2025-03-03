import { Component, OnInit } from "@angular/core"
import { EnvironmentService } from "../services/enviroment.service"
import { ApolloManagerService } from "../services/apollo-manager-service"
import { GraphQlClient, QueryConfig } from "../services/graphql-client"
import { EnvironmentInterface } from "../../environments/environment-interface"
import { LoadingService } from "../services/Loading.service"
import { TuiAlertService } from "@taiga-ui/core"
import { BaseHistory, SolverDailyHistory } from "../models"
import { catchError, map, Observable, shareReplay, zip } from "rxjs"
import { GroupedHistory } from "../groupedHistory"
import BigNumber from "bignumber.js"
import { aggregateSolverDailyHistories } from "../utils/aggregate-utils"
import { aggregateHistories, collectAllDates, justifyHistoriesToDates } from "../utils/common-utils"

@Component({
    selector: "app-solvers-charts",
    templateUrl: "./solvers-charts.component.html",
    styleUrls: ["./solvers-charts.component.scss"],
    standalone: false
})
export class SolversChartsComponent implements OnInit {
	groupedHistories?: Observable<GroupedHistory[]>
	environments: EnvironmentInterface[]

	constructor(
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		readonly apolloService: ApolloManagerService,
		protected readonly alert: TuiAlertService,
	) {
		this.environments = environmentService.getValue("environments")
	}

	ngOnInit(): void {
		const flatSolvers = this.environments.map((env: EnvironmentInterface) => env.solvers!).flat()
		this.groupedHistories = zip(
			this.environments
				.map((env: EnvironmentInterface) => {
					return env.solvers!.map(solver => {
						return {
							solver: solver,
							env: env,
							graphQlClient: new GraphQlClient(this.apolloService.getClient(env.subgraphUrl!)!, this.loadingService),
						}
					})
				})
				.flat()
				.map(context => {
					const configs: QueryConfig<any>[] = [
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
									value: `"${context.solver.address!.toLowerCase()}"`,
								},
							],
							createFunction: (obj: any) => SolverDailyHistory.fromRawObject(obj).applyDecimals(context.env.collateralDecimal!),
						},
					]
					return context.graphQlClient.loadAll(configs, 1000).pipe(map(result => result["solverDailyHistories"] || []))
				}),
		).pipe(
			catchError(err => {
				this.loadingService.setLoading(false)
				this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
				throw err
			}),
			map(solverHistoriesArrays => {
				const out: GroupedHistory[] = []
				for (let i = 0; i < solverHistoriesArrays.length; i++) {
					const solverHistory = solverHistoriesArrays[i]
					flatSolvers[i].id = i
					if (solverHistory.length > 0)
						out.push({
							index: flatSolvers[i],
							dailyHistories: solverHistory,
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

	moneyValueFormatter(x: any) {
		return BigNumber(x).toFormat(3)
	}
}
