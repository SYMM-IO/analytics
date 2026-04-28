import { Component, DestroyRef, EventEmitter, Input, OnInit, Output, inject } from "@angular/core"
import { takeUntilDestroyed } from "@angular/core/rxjs-interop"
import { GroupedHistory } from "../groupedHistory"
import { EnvironmentService } from "../services/enviroment.service"
import { GraphQlClient, QueryConfig } from "../services/graphql-client"
import { Affiliate, EnvironmentInterface } from "../../environments/environment-interface"
import { LoadingService } from "../services/Loading.service"
import { BehaviorSubject, catchError, combineLatest, Observable, of, shareReplay, zip } from "rxjs"
import { map, tap } from "rxjs/operators"
import { TuiAlertService } from "@taiga-ui/core"
import { MonthlyHistory, WeeklyHistory } from "../models"
import { aggregateMonthlyHistories, aggregateWeeklyHistories } from "../utils/aggregate-utils"
import BigNumber from "bignumber.js"
import { aggregateHistories, collectAllDates, justifyHistoriesToDates } from "../utils/common-utils"

type AffiliatePeriodHistoryResult = {
	environmentName: string
	affiliate: Affiliate
	monthlyHistories: MonthlyHistory[]
	weeklyHistories: WeeklyHistory[]
}

@Component({
    selector: "app-affiliates-charts",
    templateUrl: "./affiliates-charts.component.html",
    styleUrls: ["./affiliates-charts.component.scss"],
    standalone: false
})
export class AffiliatesChartsComponent implements OnInit {
	@Input() groupedHistories!: Observable<GroupedHistory[]>
	@Input() decimalsMap!: Map<string, number>
	@Input() set selectedChainNames(value: string[] | null | undefined) {
		this.selectedChainNames$.next(value ? [...value] : [])
	}
	@Input() set selectedFrontendNames(value: string[] | null | undefined) {
		this._selectedFrontendNames = value ? [...value] : []
		this.selectedFrontendNames$.next(this._selectedFrontendNames)
	}
	get selectedFrontendNames(): string[] {
		return this._selectedFrontendNames
	}
	@Output() totalMonthlyHistory = new EventEmitter<MonthlyHistory>()

	environments: EnvironmentInterface[]
	private _selectedFrontendNames: string[] = []
	private readonly destroyRef = inject(DestroyRef)
	private readonly selectedChainNames$ = new BehaviorSubject<string[]>([])
	private readonly selectedFrontendNames$ = new BehaviorSubject<string[]>([])

	constructor(
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		protected readonly alert: TuiAlertService,
	) {
		this.environments = environmentService.getValue("environments")
	}

	ngOnInit(): void {
		const baseGroupedHistories = this.groupedHistories

		// Only fetch data within the max UI range (730 days) to avoid loading years of unused history
		const maxRangeDays = 730
		const minFetchTimestamp = Math.floor((Date.now() - maxRangeDays * 24 * 60 * 60 * 1000) / 1000).toString()

		const environmentResults$ = zip(
			this.environments.map((env: EnvironmentInterface) => {
				const graphQlClient = new GraphQlClient(env.subgraphUrl!, this.loadingService)

				const configSets = env.affiliates!.map(aff => ({
					configs: [
						{
							method: "monthlyHistories",
							fields: ["id", "timestamp", "tradeVolume", "activeUsers", "accountSource"],
							first: 1000,
							orderBy: "timestamp",
							conditions: [
								{
									field: "accountSource",
									operator: "contains",
									value: `"${aff.address!.toLowerCase()}"`,
								},
							],
							createFunction: (obj: any) => MonthlyHistory.fromRawObject(obj).applyDecimals(env.collateralDecimal!),
						},
						{
							method: "weeklyHistories",
							fields: ["id", "timestamp", "tradeVolume", "activeUsers", "accountSource"],
							first: 1000,
							orderBy: "timestamp",
							conditions: [
								{
									field: "accountSource",
									operator: "contains",
									value: `"${aff.address!.toLowerCase()}"`,
								},
							],
							createFunction: (obj: any) => WeeklyHistory.fromRawObject(obj).applyDecimals(env.collateralDecimal!),
						},
					] as QueryConfig<any>[],
					startPaginationFields: {
						monthlyHistories: minFetchTimestamp,
						weeklyHistories: minFetchTimestamp,
					},
				}))

				return this.loadEnvironmentResults(
					env,
					graphQlClient.batchLoadAll(configSets, 1000).pipe(
						map(results =>
							results.map((result, index) => ({
								environmentName: env.name,
								affiliate: env.affiliates![index],
								monthlyHistories: result["monthlyHistories"] || [],
								weeklyHistories: result["weeklyHistories"] || [],
							})),
						),
					),
					() =>
						env.affiliates!.map(affiliate => ({
							environmentName: env.name,
							affiliate,
							monthlyHistories: [],
							weeklyHistories: [],
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

		// Frontend filter is applied at the chart level via legend.selected (smooth animation),
		// not in the data pipeline. Filtering data here would force ECharts to replaceMerge series
		// on every toggle, causing a visible flicker.
		this.groupedHistories = combineLatest([baseGroupedHistories, environmentResults$, this.selectedChainNames$]).pipe(
			map(([value, environmentResults, selectedChainNames]) => {
				const selectedChainsSet = new Set(selectedChainNames)
				const filteredResults = environmentResults.filter(
					result => selectedChainsSet.has(result.environmentName),
				)
				const newValue: GroupedHistory[] = value.map(groupedHistory => ({
					index: { ...groupedHistory.index },
					dailyHistories: groupedHistory.dailyHistories.map(dh => ({ ...dh })),
					weeklyHistories: groupedHistory.weeklyHistories.map(wh => ({ ...wh })),
					monthlyHistories: groupedHistory.monthlyHistories.map(mh => ({ ...mh })),
				})) as any

				for (const result of filteredResults) {
					newValue.push({
						dailyHistories: [],
						monthlyHistories: result.monthlyHistories,
						weeklyHistories: result.weeklyHistories,
						index: result.affiliate,
					})
				}

				return newValue
			}),
			map((affiliateHistories: GroupedHistory[]) => {
				affiliateHistories.forEach(affiliateHistory => {
					if (affiliateHistory.weeklyHistories.length > 0)
						affiliateHistory.weeklyHistories = justifyHistoriesToDates(
							affiliateHistory.weeklyHistories || [],
							collectAllDates(affiliateHistories, "weeklyHistories"),
						)
					if (affiliateHistory.monthlyHistories.length > 0)
						affiliateHistory.monthlyHistories = justifyHistoriesToDates(
							affiliateHistory.monthlyHistories || [],
							collectAllDates(affiliateHistories, "monthlyHistories"),
						)
				})
				return affiliateHistories
			}),
			map((affiliateHistories: GroupedHistory[]) => {
				const map = new Map<string, GroupedHistory>()
				for (const affiliateHistory of affiliateHistories) {
					const affiliate = affiliateHistory.index.name!
					if (map.has(affiliate)) {
						let existingHistory = map.get(affiliate)!

						existingHistory.weeklyHistories = aggregateHistories(
							affiliateHistory.weeklyHistories || [],
							existingHistory.weeklyHistories || [],
							aggregateWeeklyHistories,
						)
						existingHistory.monthlyHistories = aggregateHistories(
							affiliateHistory.monthlyHistories || [],
							existingHistory.monthlyHistories || [],
							aggregateMonthlyHistories,
						)

						map.set(affiliate, existingHistory)
					} else {
						map.set(affiliate, affiliateHistory)
					}
				}
				return [...map.values()]
			}),
			shareReplay(1),
		)

		// monthlyActiveUsers in the info card respects the frontend filter (intersection with the
		// unfiltered grouped histories). Done as a separate subscription so the chart pipeline
		// above stays stable across frontend toggles.
		combineLatest([this.groupedHistories, this.selectedFrontendNames$])
			.pipe(takeUntilDestroyed(this.destroyRef))
			.subscribe(([affiliateHistories, frontends]) => {
				const fs = new Set(frontends)
				const lastMonthEntries = affiliateHistories
					.filter(ah => !!ah.index.name && fs.has(ah.index.name))
					.map(ah => {
						const m = ah.monthlyHistories
						return m.length >= 2 ? m[m.length - 2] : null
					})
					.filter(Boolean) as MonthlyHistory[]

				if (lastMonthEntries.length > 0) {
					this.totalMonthlyHistory.emit(aggregateMonthlyHistories(lastMonthEntries))
				} else {
					this.totalMonthlyHistory.emit(new MonthlyHistory())
				}
			})
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
