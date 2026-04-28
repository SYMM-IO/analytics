import { ChangeDetectorRef, Component, DestroyRef, Inject, OnDestroy, OnInit, inject } from "@angular/core"
import { takeUntilDestroyed } from "@angular/core/rxjs-interop"
import { catchError, combineLatest, Observable, of, shareReplay, tap, zip } from "rxjs"
import { map } from "rxjs/operators"
import { GraphQlClient, QueryConfig } from "../services/graphql-client"
import { LoadingService } from "../services/Loading.service"
import { EnvironmentService } from "../services/enviroment.service"
import { FilterToolbarService } from "../services/filter-toolbar.service"
import { Affiliate, EnvironmentInterface } from "../../environments/environment-interface"
import { TuiAlertService } from "@taiga-ui/core"
import { BaseHistory, DailyHistory, TotalHistory } from "../models"
import { aggregateDailyHistories, aggregateTotalHistories } from "../utils/aggregate-utils"
import { GroupedHistory } from "../groupedHistory"
import { aggregateHistories, collectAllDates, justifyHistoriesToDates } from "../utils/common-utils"
import BigNumber from "bignumber.js"

type EnvironmentHistoryResult = {
	environmentName: string
	affiliate: Affiliate
	dailyHistories: DailyHistory[]
	totalHistories: TotalHistory[]
}

export enum ViewMode {
	SOLVERS = "SOLVERS",
	FRONTENDS = "FRONTENDS",
}

@Component({
    selector: "app-home",
    templateUrl: "./home.component.html",
    styleUrls: ["./home.component.scss"],
    standalone: false
})
export class HomeComponent implements OnInit, OnDestroy {
	groupedHistories?: Observable<GroupedHistory[]>
	totalHistory?: TotalHistory
	todayHistory?: DailyHistory
	lastMonthHistory?: DailyHistory
	environments: EnvironmentInterface[]
	decimalsMap = new Map<string, number>()
	ViewMode = ViewMode
	get viewMode(): ViewMode { return this.filterToolbar.view as ViewMode }
	monthlyActiveUsers: any
	zero = BigNumber(0)
	depositsSpark: number[] = []
	volumeSpark: number[] = []
	quotesSpark: number[] = []
	usersSpark: number[] = []
	private readonly destroyRef = inject(DestroyRef)
	private readonly SPARK_DAYS = 60

	get selectedChainNames(): string[] { return this.filterToolbar.selectedChainNames }
	get selectedFrontendNames(): string[] { return this.filterToolbar.selectedFrontendNames }

	constructor(
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		readonly filterToolbar: FilterToolbarService,
		@Inject(TuiAlertService) protected readonly alert: TuiAlertService,
		private cdr: ChangeDetectorRef,
	) {
		this.environments = environmentService.getValue("environments")
		for (const env of this.environments)
			for (const affiliate of env.affiliates!) this.decimalsMap.set(affiliate.address!.toLowerCase(), env.collateralDecimal!)

		this.environmentService.loadedSubgraphs
			.pipe(takeUntilDestroyed())
			.subscribe(loadedChainNames => {
				// Initial order is alphabetical (predictable while volume data is still loading).
				// After environmentResults$ emits, this gets re-sorted by trade volume below.
				const alpha = [...loadedChainNames].sort((a, b) => a.localeCompare(b))
				this.filterToolbar.setLoadedChains(alpha)
				const frontends = this.getFrontendNamesForChains(alpha).sort((a, b) => a.localeCompare(b))
				this.filterToolbar.setAvailableFrontends(frontends)
				this.cdr.markForCheck()
			})

		this.environmentService.ignoredSubgraphNames
			.pipe(takeUntilDestroyed())
			.subscribe(ignoredChainNames => {
				this.filterToolbar.setIgnoredChains(ignoredChainNames)
				this.cdr.markForCheck()
			})

		this.filterToolbar.selectedChainNames$
			.pipe(takeUntilDestroyed())
			.subscribe(() => this.cdr.markForCheck())

		this.filterToolbar.selectedFrontendNames$
			.pipe(takeUntilDestroyed())
			.subscribe(() => this.cdr.markForCheck())

		this.filterToolbar.view$
			.pipe(takeUntilDestroyed())
			.subscribe(() => this.cdr.markForCheck())
	}

	ngOnInit(): void {
		this.filterToolbar.setVisible(true)

		// Only fetch data within the max UI range (730 days = "All" option) to avoid loading years of unused history
		const maxRangeDays = 730
		const minFetchTimestamp = Math.floor((Date.now() - maxRangeDays * 24 * 60 * 60 * 1000) / 1000).toString()

		const environmentResults$ = zip(
			this.environments.map((env: EnvironmentInterface) => {
				const graphQlClient = new GraphQlClient(env.subgraphUrl!, this.loadingService)
				let collaterals = env.collaterals!.map(c => `\"${c.toLowerCase()}\"`).join(",")

				const configSets = env.affiliates!.map(aff => {
					const dailyFromTimestamp = aff.fromTimestamp || minFetchTimestamp
					return {
						configs: [
							{
								method: "dailyHistories",
								fields: [
									"id",
									"tradeVolume",
									"liquidateTradeVolume",
									"averagePositionSize",
									"quotesCount",
									"newUsers",
									"activeUsers",
									"newAccounts",
									"deposit",
									"platformFee",
									"openInterest",
									"accountSource",
									"timestamp",
								],
								first: 1000,
								orderBy: "timestamp",
								conditions: [
									{
										field: "accountSource",
										operator: "contains",
										value: `"${aff.address!.toLowerCase()}"`,
									},
								],
								createFunction: (obj: any) => DailyHistory.fromRawObject(obj).applyDecimals(env.collateralDecimal!),
							},
							{
								method: "totalHistories",
								fields: ["id", "users", "accounts", "deposit", "tradeVolume", "quotesCount", "accountSource", "timestamp"],
								first: 1000,
								orderBy: "timestamp",
								conditions: [
									{
										field: "accountSource",
										operator: "contains",
										value: `"${aff.address!.toLowerCase()}"`,
									},
									{
										field: "collateral",
										operator: "in",
										value: `[${collaterals}]`,
									},
								],
								createFunction: (obj: any) => TotalHistory.fromRawObject(obj).applyDecimals(env.collateralDecimal!),
							},
						] as QueryConfig<any>[],
						startPaginationFields: {
							dailyHistories: dailyFromTimestamp,
							totalHistories: "0",
						},
					}
				})

				return this.loadEnvironmentResults(
					env,
					graphQlClient.batchLoadAll(configSets, 1000).pipe(
						map(results =>
							results.map((result, index) => ({
								environmentName: env.name,
								affiliate: env.affiliates![index],
								dailyHistories: result["dailyHistories"] || [],
								totalHistories: result["totalHistories"] || [],
							})),
						),
					),
					() =>
						env.affiliates!.map(affiliate => ({
							environmentName: env.name,
							affiliate,
							dailyHistories: [],
							totalHistories: [],
						})),
				)
			}),
		).pipe(map(envResults => envResults.flat()), shareReplay(1))

		const chainFilteredEnvResults$ = combineLatest([environmentResults$, this.filterToolbar.selectedChainNames$]).pipe(
			map(([results, chains]) => {
				const selectedChainsSet = new Set(chains)
				return results.filter(result => selectedChainsSet.has(result.environmentName))
			}),
			catchError(err => {
				this.loadingService.setLoading(false)
				this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
				throw err
			}),
			shareReplay(1),
		)

		// Info cards reflect both chain AND frontend filters. Computed in a separate stream so
		// toggling the frontend filter doesn't re-emit groupedHistories — that re-emission would
		// trigger the ECharts series replaceMerge flicker. Chart visibility is handled inside
		// chart.component via legend.selected (smooth, animated).
		combineLatest([chainFilteredEnvResults$, this.filterToolbar.selectedFrontendNames$])
			.pipe(takeUntilDestroyed(this.destroyRef))
			.subscribe(([envResults, frontends]) => {
				const fs = new Set(frontends)
				const filtered = envResults.filter(r => !!r.affiliate.name && fs.has(r.affiliate.name))

				const totalHistories: TotalHistory[] = filtered.flatMap(r => r.totalHistories).filter(th => th != null)
				this.totalHistory = totalHistories.length > 0 ? aggregateTotalHistories(totalHistories) : undefined

				const aggregated = this.aggregateAffiliateHistories(filtered)
				const latestHistories = aggregated.map(a => a.dailyHistories[a.dailyHistories.length - 1] as DailyHistory).filter(Boolean)
				this.todayHistory = latestHistories.length > 0 ? aggregateDailyHistories(latestHistories) : undefined

				const lastMonth = aggregated.map(a => this.getLastCalendarMonthHistories(a.dailyHistories)).flat()
				this.lastMonthHistory = lastMonth.length > 0 ? aggregateDailyHistories(lastMonth) : undefined

				this.refreshSparklines(aggregated)

				this.cdr.markForCheck()
			})

		this.groupedHistories = chainFilteredEnvResults$.pipe(
			map(envResults => this.aggregateAffiliateHistories(envResults)),
			shareReplay(1),
		)

		// Once environment results are in, re-sort the chain & frontend filter lists by total
		// trade volume (descending). Alphabetical sort applied earlier remains the fallback if
		// this never fires.
		environmentResults$
			.pipe(takeUntilDestroyed(this.destroyRef))
			.subscribe(envResults => {
				const chainVolume = new Map<string, BigNumber>()
				const frontendVolume = new Map<string, BigNumber>()

				for (const r of envResults) {
					const total = r.totalHistories.reduce(
						(acc, h) => acc.plus(h.tradeVolume ?? BigNumber(0)),
						BigNumber(0),
					)
					chainVolume.set(
						r.environmentName,
						(chainVolume.get(r.environmentName) ?? BigNumber(0)).plus(total),
					)
					if (r.affiliate.name) {
						frontendVolume.set(
							r.affiliate.name,
							(frontendVolume.get(r.affiliate.name) ?? BigNumber(0)).plus(total),
						)
					}
				}

				const byVolume = (vols: Map<string, BigNumber>) => (a: string, b: string): number => {
					const cmp = (vols.get(b) ?? BigNumber(0)).comparedTo(vols.get(a) ?? BigNumber(0)) ?? 0
					return cmp !== 0 ? cmp : a.localeCompare(b)
				}

				const sortedChains = [...this.filterToolbar.loadedChainNames].sort(byVolume(chainVolume))
				this.filterToolbar.setLoadedChains(sortedChains)

				const sortedFrontends = this.getFrontendNamesForChains(sortedChains).sort(byVolume(frontendVolume))
				this.filterToolbar.setAvailableFrontends(sortedFrontends)
			})
	}

	ngOnDestroy(): void {
		this.filterToolbar.setVisible(false)
	}


	private aggregateAffiliateHistories(environmentResults: EnvironmentHistoryResult[]): GroupedHistory[] {
		const out: GroupedHistory[] = []
		for (const result of environmentResults) {
			if (result.dailyHistories.length > 0)
				out.push({
					index: result.affiliate,
					dailyHistories: result.dailyHistories,
					weeklyHistories: [],
					monthlyHistories: [],
				})
		}

		const all_dates = collectAllDates(out, "dailyHistories")
		out.forEach(groupedHistory => {
			const mapped_data = new Map<number, DailyHistory>()
			for (const history of groupedHistory.dailyHistories) {
				const time = BaseHistory.getTime(history)!
				if (mapped_data.has(time)) {
					const lastHistory = mapped_data.get(time)!
					const aggregatedHistory = aggregateDailyHistories([lastHistory, history])
					aggregatedHistory.timestamp = lastHistory.timestamp! >= history.timestamp! ? lastHistory.timestamp : history.timestamp
					mapped_data.set(time, aggregatedHistory)
				} else {
					mapped_data.set(time, history)
				}
			}
			groupedHistory.dailyHistories = justifyHistoriesToDates([...mapped_data.values()], all_dates)
		})

		const byName = new Map<string, GroupedHistory>()
		for (const affiliateHistory of out) {
			const affiliate = affiliateHistory.index.name!
			if (byName.has(affiliate)) {
				const existingHistory = byName.get(affiliate)!
				existingHistory.dailyHistories = aggregateHistories(
					affiliateHistory.dailyHistories,
					existingHistory.dailyHistories,
					aggregateDailyHistories,
				)
				byName.set(affiliate, existingHistory)
			} else {
				byName.set(affiliate, affiliateHistory)
			}
		}
		return [...byName.values()]
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

	private getFrontendNamesForChains(chainNames: string[]): string[] {
		const names = new Set<string>()
		const chainNameSet = new Set(chainNames)
		for (const env of this.environments) {
			if (!chainNameSet.has(env.name)) continue
			for (const affiliate of env.affiliates ?? []) {
				if (affiliate.name) names.add(affiliate.name)
			}
		}
		return [...names]
	}

	private refreshSparklines(aggregated: GroupedHistory[]): void {
		// Sum daily histories across affiliates by timestamp, then take the last N days.
		const byTime = new Map<number, { deposit: BigNumber; volume: BigNumber; quotes: BigNumber; users: BigNumber }>()
		for (const ah of aggregated) {
			for (const raw of ah.dailyHistories) {
				const d = raw as DailyHistory
				const t = DailyHistory.getTime(d)
				if (t == null) continue
				const slot = byTime.get(t) ?? { deposit: BigNumber(0), volume: BigNumber(0), quotes: BigNumber(0), users: BigNumber(0) }
				slot.deposit = slot.deposit.plus(d.deposit ?? BigNumber(0))
				slot.volume = slot.volume.plus(d.tradeVolume ?? BigNumber(0))
				slot.quotes = slot.quotes.plus(d.quotesCount ?? BigNumber(0))
				slot.users = slot.users.plus(d.activeUsers ?? BigNumber(0))
				byTime.set(t, slot)
			}
		}
		const sorted = [...byTime.entries()].sort((a, b) => a[0] - b[0])
		const tail = sorted.slice(-this.SPARK_DAYS)
		this.depositsSpark = tail.map(([, v]) => v.deposit.toNumber())
		this.volumeSpark = tail.map(([, v]) => v.volume.toNumber())
		this.quotesSpark = tail.map(([, v]) => v.quotes.toNumber())
		this.usersSpark = tail.map(([, v]) => v.users.toNumber())
	}

	private getLastCalendarMonthHistories(histories: DailyHistory[]): DailyHistory[] {
		const now = new Date()
		const lastMonth = now.getMonth() === 0 ? 11 : now.getMonth() - 1
		const yearOfLastMonth = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()

		const startOfLastMonth = new Date(yearOfLastMonth, lastMonth, 1)
		const startOfThisMonth = new Date(now.getFullYear(), now.getMonth(), 1)

		const startOfLastMonthTimestamp = Math.floor(startOfLastMonth.getTime() / 1000)
		const startOfThisMonthTimestamp = Math.floor(startOfThisMonth.getTime() / 1000)

		return histories.filter(daily => {
			const ts = DailyHistory.getTime(daily)! / 1000
			return ts >= startOfLastMonthTimestamp && ts < startOfThisMonthTimestamp
		})
	}
}
