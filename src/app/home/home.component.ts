import { ChangeDetectorRef, Component, DestroyRef, Inject, OnDestroy, OnInit, inject } from "@angular/core"
import { takeUntilDestroyed } from "@angular/core/rxjs-interop"
import { catchError, combineLatest, Observable, of, shareReplay, tap, zip } from "rxjs"
import { map } from "rxjs/operators"
import { GraphQlClient, QueryConfig } from "../services/graphql-client"
import { LoadingService } from "../services/Loading.service"
import { EnvironmentService } from "../services/enviroment.service"
import { FilterToolbarService, OTHERS_FRONTEND_COLOR, OTHERS_FRONTEND_NAME } from "../services/filter-toolbar.service"
import { Affiliate, EnvironmentInterface } from "../../environments/environment-interface"
import { TuiAlertService } from "@taiga-ui/core"
import { BaseHistory, DailyHistory, TotalHistory } from "../models"
import { aggregateDailyHistories, aggregateTotalHistories } from "../utils/aggregate-utils"
import { GroupedHistory } from "../groupedHistory"
import { aggregateHistories, collectAllDates, justifyHistoriesToDates } from "../utils/common-utils"
import { normalizeAddress, resolveAffiliate } from "../utils/entity-utils"
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
	standalone: false,
})
export class HomeComponent implements OnInit, OnDestroy {
	groupedHistories?: Observable<GroupedHistory[]>
	totalHistory?: TotalHistory
	legacyTotalHistory?: TotalHistory
	todayHistory?: DailyHistory
	lastMonthHistory?: DailyHistory
	legacyLastMonthHistory?: DailyHistory
	environments: EnvironmentInterface[]
	decimalsMap = new Map<string, number>()
	ViewMode = ViewMode
	get viewMode(): ViewMode {
		return this.filterToolbar.view as ViewMode
	}
	monthlyActiveUsers: any
	zero = BigNumber(0)
	depositsSpark: number[] = []
	volumeSpark: number[] = []
	quotesSpark: number[] = []
	usersSpark: number[] = []
	private readonly destroyRef = inject(DestroyRef)
	private readonly SPARK_DAYS = 60

	get selectedChainNames(): string[] {
		return this.filterToolbar.selectedChainNames
	}
	get selectedFrontendNames(): string[] {
		return this.filterToolbar.selectedFrontendNames
	}

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

		this.environmentService.loadedSubgraphs.pipe(takeUntilDestroyed()).subscribe(loadedChainNames => {
			const alpha = [...loadedChainNames].sort((a, b) => a.localeCompare(b))
			this.filterToolbar.setLoadedChains(alpha)
			this.cdr.markForCheck()
		})

		this.environmentService.ignoredSubgraphNames.pipe(takeUntilDestroyed()).subscribe(ignoredChainNames => {
			this.filterToolbar.setIgnoredChains(ignoredChainNames)
			this.cdr.markForCheck()
		})

		this.filterToolbar.selectedChainNames$.pipe(takeUntilDestroyed()).subscribe(() => this.cdr.markForCheck())

		this.filterToolbar.selectedFrontendNames$.pipe(takeUntilDestroyed()).subscribe(() => this.cdr.markForCheck())

		this.filterToolbar.view$.pipe(takeUntilDestroyed()).subscribe(() => this.cdr.markForCheck())
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

				const configs: QueryConfig<any>[] = [
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
						createFunction: (obj: any) => DailyHistory.fromRawObject(obj).applyDecimals(env.collateralDecimal!),
					},
					{
						method: "totalHistories",
						fields: ["id", "users", "accounts", "deposit", "tradeVolume", "quotesCount", "accountSource", "timestamp"],
						first: 1000,
						orderBy: "timestamp",
						conditions: [
							{
								field: "collateral",
								operator: "in",
								value: `[${collaterals}]`,
							},
						],
						createFunction: (obj: any) => TotalHistory.fromRawObject(obj).applyDecimals(env.collateralDecimal!),
					},
				]

				return this.loadEnvironmentResults(
					env,
					graphQlClient
						.loadAll(configs, 1000, {
							dailyHistories: minFetchTimestamp,
							totalHistories: "0",
						})
						.pipe(
							map(result =>
								this.groupEnvironmentHistories(
									env,
									(result["dailyHistories"] || []) as DailyHistory[],
									(result["totalHistories"] || []) as TotalHistory[],
								),
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
		).pipe(
			map(envResults => envResults.flat()),
			map(envResults => this.groupLowVolumeFrontends(envResults)),
			shareReplay(1),
		)
		const legacyMetricResults$ = zip(
			this.environments.map(env => this.loadLegacyMetricEnvironmentResults(env, minFetchTimestamp)),
		).pipe(
			map(envResults => envResults.flat()),
			shareReplay(1),
		)

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
		const chainFilteredLegacyMetricResults$ = combineLatest([
			legacyMetricResults$,
			this.filterToolbar.selectedChainNames$,
		]).pipe(
			map(([results, chains]) => {
				const selectedChainsSet = new Set(chains)
				return results.filter(result => selectedChainsSet.has(result.environmentName))
			}),
			shareReplay(1),
		)

		// Info cards reflect both chain AND frontend filters. Computed in a separate stream so
		// toggling the frontend filter doesn't re-emit groupedHistories — that re-emission would
		// trigger the ECharts series replaceMerge flicker. Chart visibility is handled inside
		// chart.component via legend.selected (smooth, animated).
		combineLatest([
			chainFilteredEnvResults$,
			chainFilteredLegacyMetricResults$,
			this.filterToolbar.selectedFrontendNames$,
		])
			.pipe(takeUntilDestroyed(this.destroyRef))
			.subscribe(([envResults, legacyMetricResults, frontends]) => {
				const fs = new Set(frontends)
				const filtered = envResults.filter(r => !!r.affiliate.name && fs.has(r.affiliate.name))
				const legacyFiltered = this.filterLegacyMetricResults(legacyMetricResults, fs)

				const totalHistories: TotalHistory[] = filtered.flatMap(r => r.totalHistories).filter(th => th != null)
				this.totalHistory = totalHistories.length > 0 ? aggregateTotalHistories(totalHistories) : undefined
				const legacyTotalHistories = legacyFiltered.flatMap(r => r.totalHistories).filter(th => th != null)
				this.legacyTotalHistory =
					legacyTotalHistories.length > 0 ? aggregateTotalHistories(legacyTotalHistories) : undefined

				const aggregated = this.aggregateAffiliateHistories(filtered)
				const legacyAggregated = this.aggregateAffiliateHistories(legacyFiltered)
				const latestHistories = aggregated.map(a => a.dailyHistories[a.dailyHistories.length - 1] as DailyHistory).filter(Boolean)
				this.todayHistory = latestHistories.length > 0 ? aggregateDailyHistories(latestHistories) : undefined

				const lastMonth = aggregated.map(a => this.getLastCalendarMonthHistories(a.dailyHistories)).flat()
				this.lastMonthHistory = lastMonth.length > 0 ? aggregateDailyHistories(lastMonth) : undefined
				const legacyLastMonth = legacyAggregated.map(a => this.getLastCalendarMonthHistories(a.dailyHistories)).flat()
				this.legacyLastMonthHistory =
					legacyLastMonth.length > 0 ? aggregateDailyHistories(legacyLastMonth) : undefined

				this.refreshSparklines(aggregated, legacyAggregated)

				this.cdr.markForCheck()
			})

		this.groupedHistories = chainFilteredEnvResults$.pipe(
			map(envResults => this.aggregateAffiliateHistories(envResults)),
			shareReplay(1),
		)

		// Once environment results are in, sort the chain & frontend filter lists by total
		// trade volume (descending).
		environmentResults$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(envResults => {
			const chainVolume = new Map<string, BigNumber>()
			const frontendVolume = new Map<string, BigNumber>()

			for (const r of envResults) {
				const total = r.totalHistories.reduce((acc, h) => acc.plus(h.tradeVolume ?? BigNumber(0)), BigNumber(0))
				chainVolume.set(r.environmentName, (chainVolume.get(r.environmentName) ?? BigNumber(0)).plus(total))
				if (r.affiliate.name) {
					frontendVolume.set(r.affiliate.name, (frontendVolume.get(r.affiliate.name) ?? BigNumber(0)).plus(total))
				}
			}

			const byVolume =
				(vols: Map<string, BigNumber>) =>
				(a: string, b: string): number => {
					const cmp = (vols.get(b) ?? BigNumber(0)).comparedTo(vols.get(a) ?? BigNumber(0)) ?? 0
					return cmp !== 0 ? cmp : a.localeCompare(b)
				}

			const sortedChains = [...this.filterToolbar.loadedChainNames].sort(byVolume(chainVolume))
			this.filterToolbar.setLoadedChains(sortedChains)

			const sortedFrontends = [...frontendVolume.keys()]
				.filter(name => this.filterToolbar.hasFrontendTradeVolume(name))
				.sort(byVolume(frontendVolume))
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
				existingHistory.dailyHistories = aggregateHistories(affiliateHistory.dailyHistories, existingHistory.dailyHistories, aggregateDailyHistories)
				byName.set(affiliate, existingHistory)
			} else {
				byName.set(affiliate, affiliateHistory)
			}
		}
		return [...byName.values()]
	}

	private groupEnvironmentHistories(
		env: EnvironmentInterface,
		dailyHistories: DailyHistory[],
		totalHistories: TotalHistory[],
	): EnvironmentHistoryResult[] {
		const grouped = new Map<string, EnvironmentHistoryResult>()
		const getResult = (accountSource?: string): EnvironmentHistoryResult => {
			const affiliate = resolveAffiliate(env, accountSource)
			const address = normalizeAddress(affiliate.address)
			if (!grouped.has(address)) {
				grouped.set(address, {
					environmentName: env.name,
					affiliate,
					dailyHistories: [],
					totalHistories: [],
				})
			}
			return grouped.get(address)!
		}

		for (const history of dailyHistories) getResult(history.accountSource).dailyHistories.push(history)
		for (const history of totalHistories) getResult(history.accountSource).totalHistories.push(history)
		return [...grouped.values()]
	}

	private groupLowVolumeFrontends(environmentResults: EnvironmentHistoryResult[]): EnvironmentHistoryResult[] {
		const frontendVolumes = new Map<string, BigNumber>()
		for (const result of environmentResults) {
			if (!result.affiliate.name) continue
			const total = result.totalHistories.reduce(
				(sum, history) => sum.plus(history.tradeVolume ?? BigNumber(0)),
				BigNumber(0),
			)
			frontendVolumes.set(
				result.affiliate.name,
				(frontendVolumes.get(result.affiliate.name) ?? BigNumber(0)).plus(total),
			)
		}

		this.filterToolbar.setFrontendVolumes(
			new Map([...frontendVolumes.entries()].map(([name, volume]) => [name, volume.toFixed()])),
		)

		return environmentResults.map(result => {
			const displayName = this.filterToolbar.frontendDisplayName(result.affiliate.name)
			if (displayName === result.affiliate.name) return result
			return {
				...result,
				affiliate: {
					...result.affiliate,
					name: OTHERS_FRONTEND_NAME,
					mainColor: OTHERS_FRONTEND_COLOR,
				},
			}
		})
	}

	private filterLegacyMetricResults(
		environmentResults: EnvironmentHistoryResult[],
		selectedFrontendNames: Set<string>,
	): EnvironmentHistoryResult[] {
		const environments = new Map(this.environments.map(env => [env.name, env]))
		const availableFrontendNames = this.filterToolbar.availableFrontendNames
		return environmentResults.flatMap(result => {
			if (!result.affiliate.name) return []

			const matchingCurrentName = availableFrontendNames.find(
				name => name.toLowerCase() === result.affiliate.name!.toLowerCase(),
			)
			const env = environments.get(result.environmentName)
			const addressMappedName = env ? resolveAffiliate(env, result.affiliate.address).name : undefined
			const currentName = matchingCurrentName ?? addressMappedName ?? result.affiliate.name
			const displayName = this.filterToolbar.frontendDisplayName(currentName)
			if (!displayName || !selectedFrontendNames.has(displayName)) return []

			return [
				{
					...result,
					affiliate: { ...result.affiliate, name: displayName },
				},
			]
		})
	}

	private loadLegacyMetricEnvironmentResults(
		env: EnvironmentInterface,
		minFetchTimestamp: string,
	): Observable<EnvironmentHistoryResult[]> {
		const graphQlClient = new GraphQlClient(env.subgraphUrl!, this.loadingService)
		const collaterals = env.collaterals!.map(c => `\"${c.toLowerCase()}\"`).join(",")
		const affiliates = env.legacyMetricAffiliates ?? env.affiliates ?? []
		const configSets = affiliates.map(affiliate => {
			const dailyFromTimestamp = affiliate.fromTimestamp || minFetchTimestamp
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
								value: `"${affiliate.address!.toLowerCase()}"`,
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
								value: `"${affiliate.address!.toLowerCase()}"`,
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
			graphQlClient.batchLoadAll(configSets, 1000, { advancePartialPageCursors: false }).pipe(
				map(results =>
					results.map((result, index) => ({
						environmentName: env.name,
						affiliate: affiliates[index],
						dailyHistories: result["dailyHistories"] || [],
						totalHistories: result["totalHistories"] || [],
					})),
				),
			),
			() =>
				affiliates.map(affiliate => ({
					environmentName: env.name,
					affiliate,
					dailyHistories: [],
					totalHistories: [],
				})),
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

	private refreshSparklines(aggregated: GroupedHistory[], legacyAggregated: GroupedHistory[]): void {
		// Sum daily histories across affiliates by timestamp, then take the last N days.
		const byTime = this.aggregateSparklineValues(aggregated)
		const legacyByTime = this.aggregateSparklineValues(legacyAggregated)
		const tail = [...byTime.entries()].sort((a, b) => a[0] - b[0]).slice(-this.SPARK_DAYS)
		const legacyTail = [...legacyByTime.entries()].sort((a, b) => a[0] - b[0]).slice(-this.SPARK_DAYS)
		this.depositsSpark = legacyTail.map(([, v]) => v.deposit.toNumber())
		this.volumeSpark = legacyTail.map(([, v]) => v.volume.toNumber())
		this.quotesSpark = tail.map(([, v]) => v.quotes.toNumber())
		this.usersSpark = tail.map(([, v]) => v.users.toNumber())
	}

	private aggregateSparklineValues(
		aggregated: GroupedHistory[],
	): Map<number, { deposit: BigNumber; volume: BigNumber; quotes: BigNumber; users: BigNumber }> {
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
		return byTime
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
