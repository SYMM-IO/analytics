import { ChangeDetectorRef, Component, DestroyRef, HostListener, Inject, OnInit, inject } from "@angular/core"
import { takeUntilDestroyed } from "@angular/core/rxjs-interop"
import { catchError, combineLatest, BehaviorSubject, Observable, of, shareReplay, tap, zip } from "rxjs"
import { map } from "rxjs/operators"
import { GraphQlClient, QueryConfig } from "../services/graphql-client"
import { LoadingService } from "../services/Loading.service"
import { EnvironmentService } from "../services/enviroment.service"
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
export class HomeComponent implements OnInit {
	groupedHistories?: Observable<GroupedHistory[]>
	totalHistory?: TotalHistory
	todayHistory?: DailyHistory
	lastMonthHistory?: DailyHistory
	environments: EnvironmentInterface[]
	decimalsMap = new Map<string, number>()
	ViewMode = ViewMode
	viewMode: ViewMode = ViewMode.FRONTENDS
	monthlyActiveUsers: any
	zero  = BigNumber(0)
	loadedChainNames: string[] = []
	ignoredChainNames: string[] = []
	selectedChainNames: string[] = []
	availableFrontendNames: string[] = []
	selectedFrontendNames: string[] = []
	chainDropdownOpen = false
	frontendDropdownOpen = false
	private readonly selectedChainNames$ = new BehaviorSubject<string[]>([])
	private readonly selectedFrontendNames$ = new BehaviorSubject<string[]>([])
	private readonly destroyRef = inject(DestroyRef)
	hasCustomizedChainSelection = false
	hasCustomizedFrontendSelection = false

	private static readonly CHAIN_LOGOS: Record<string, string> = {
		fantom: "assets/chains/fantom.svg",
		bnb: "assets/chains/binance.svg",
		binance: "assets/chains/binance.svg",
		base: "assets/chains/base.png",
		blast: "assets/chains/blast.svg",
		mantle: "assets/chains/mantle.svg",
		arbitrum: "assets/chains/arbitrum.png",
		sonic: "assets/chains/sonic.svg",
		hyperevm: "assets/chains/hyperevm.svg",
	}

	private static readonly FRONTEND_LOGOS: Record<string, string> = {
		intentx: "assets/frontends/intentx-rounded-branded.svg",
		thena: "assets/frontends/thena-rounded-branded.svg",
		befi: "assets/frontends/befi-labs-rounded-branded.svg",
		cloverfield: "assets/frontends/cloverfield-rounded-branded.svg",
		core: "assets/frontends/core-rounded-branded.svg",
		bmx: "assets/frontends/bmx-rounded-branded.svg",
		privex: "assets/frontends/privex-rounded-branded.svg",
		pear: "assets/frontends/pear-rounded-branded.svg",
		based: "assets/frontends/based-rounded-branded.svg",
		xpanse: "assets/frontends/xpanse-rounded-branded.svg",
		ivx: "assets/frontends/ivx-rounded-branded.svg",
		lode: "assets/frontends/lode-rounded-branded.svg",
		spooky: "assets/frontends/spooky-rounded-branded.svg",
		vibe: "assets/frontends/vibe-rounded-branded.svg",
		carbon: "assets/frontends/carbon-rounded-branded.svg",
		quickswap: "assets/frontends/quickswap-rounded-branded.svg",
		treble: "assets/frontends/treble-rounded-branded.svg",
	}

	chainLogo(name: string): string | null {
		return HomeComponent.CHAIN_LOGOS[name.toLowerCase()] ?? null
	}

	frontendLogo(name: string): string | null {
		return HomeComponent.FRONTEND_LOGOS[name.toLowerCase()] ?? null
	}

	chainInitials(name: string): string {
		return name.slice(0, 2).toUpperCase()
	}
	constructor(
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		@Inject(TuiAlertService) protected readonly alert: TuiAlertService,
		private cdr: ChangeDetectorRef,
	) {
		this.environments = environmentService.getValue("environments")
		for (const env of this.environments)
			for (const affiliate of env.affiliates!) this.decimalsMap.set(affiliate.address!.toLowerCase(), env.collateralDecimal!)

		this.environmentService.loadedSubgraphs
			.pipe(takeUntilDestroyed())
			.subscribe(loadedChainNames => {
				this.loadedChainNames = loadedChainNames

				if (!this.hasCustomizedChainSelection) {
					this.selectedChainNames = [...loadedChainNames]
				} else {
					const loadedChainsSet = new Set(loadedChainNames)
					this.selectedChainNames = this.selectedChainNames.filter(chainName => loadedChainsSet.has(chainName))
				}

				this.selectedChainNames$.next([...this.selectedChainNames])
				this.syncAvailableFrontends(loadedChainNames)
				this.cdr.markForCheck()
			})

		this.environmentService.ignoredSubgraphNames
			.pipe(takeUntilDestroyed())
			.subscribe(ignoredChainNames => {
				this.ignoredChainNames = ignoredChainNames
				this.cdr.markForCheck()
			})
	}

	ngOnInit(): void {
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

		const chainFilteredEnvResults$ = combineLatest([environmentResults$, this.selectedChainNames$]).pipe(
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
		combineLatest([chainFilteredEnvResults$, this.selectedFrontendNames$])
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

				this.cdr.markForCheck()
			})

		this.groupedHistories = chainFilteredEnvResults$.pipe(
			map(envResults => this.aggregateAffiliateHistories(envResults)),
			shareReplay(1),
		)
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

	toggleChainDropdown() {
		if (this.loadedChainNames.length === 0 && this.ignoredChainNames.length === 0) return
		this.chainDropdownOpen = !this.chainDropdownOpen
		if (this.chainDropdownOpen) this.frontendDropdownOpen = false
	}

	toggleFrontendDropdown() {
		if (this.availableFrontendNames.length === 0) return
		this.frontendDropdownOpen = !this.frontendDropdownOpen
		if (this.frontendDropdownOpen) this.chainDropdownOpen = false
	}

	toggleChain(chainName: string) {
		const selectedChains = new Set(this.selectedChainNames)
		if (selectedChains.has(chainName)) {
			selectedChains.delete(chainName)
		} else {
			selectedChains.add(chainName)
		}
		this.hasCustomizedChainSelection = true
		this.selectedChainNames = this.loadedChainNames.filter(name => selectedChains.has(name))
		this.selectedChainNames$.next([...this.selectedChainNames])
		this.cdr.markForCheck()
	}

	selectAllChains() {
		this.hasCustomizedChainSelection = false
		this.selectedChainNames = [...this.loadedChainNames]
		this.selectedChainNames$.next([...this.selectedChainNames])
		this.cdr.markForCheck()
	}

	clearChainSelection() {
		this.hasCustomizedChainSelection = true
		this.selectedChainNames = []
		this.selectedChainNames$.next([])
		this.cdr.markForCheck()
	}

	isChainSelected(chainName: string): boolean {
		return this.selectedChainNames.includes(chainName)
	}

	removeChain(chainName: string) {
		if (!this.isChainSelected(chainName)) return
		this.toggleChain(chainName)
	}

	toggleFrontend(frontendName: string) {
		const selectedFrontends = new Set(this.selectedFrontendNames)
		if (selectedFrontends.has(frontendName)) {
			selectedFrontends.delete(frontendName)
		} else {
			selectedFrontends.add(frontendName)
		}
		this.hasCustomizedFrontendSelection = true
		this.selectedFrontendNames = this.availableFrontendNames.filter(name => selectedFrontends.has(name))
		this.selectedFrontendNames$.next([...this.selectedFrontendNames])
		this.cdr.markForCheck()
	}

	selectAllFrontends() {
		this.hasCustomizedFrontendSelection = false
		this.selectedFrontendNames = [...this.availableFrontendNames]
		this.selectedFrontendNames$.next([...this.selectedFrontendNames])
		this.cdr.markForCheck()
	}

	clearFrontendSelection() {
		this.hasCustomizedFrontendSelection = true
		this.selectedFrontendNames = []
		this.selectedFrontendNames$.next([])
		this.cdr.markForCheck()
	}

	isFrontendSelected(frontendName: string): boolean {
		return this.selectedFrontendNames.includes(frontendName)
	}

	removeFrontend(frontendName: string) {
		if (!this.isFrontendSelected(frontendName)) return
		this.toggleFrontend(frontendName)
	}

	onFilterDropdownWheel(event: WheelEvent) {
		const dropdown = event.currentTarget as HTMLElement
		const target = event.target as HTMLElement
		const list = target.closest(".filter-dropdown-list") as HTMLElement | null || dropdown.querySelector(".filter-dropdown-list")
		this.scrollDropdownList(event, list)
	}

	@HostListener("document:click", ["$event"])
	onDocumentClick(event: MouseEvent) {
		const target = event.target as HTMLElement
		const chainDropdownContainer = target.closest(".chain-filter-container")
		if (!chainDropdownContainer && this.chainDropdownOpen) {
			this.chainDropdownOpen = false
		}

		const frontendDropdownContainer = target.closest(".frontend-filter-container")
		if (!frontendDropdownContainer && this.frontendDropdownOpen) {
			this.frontendDropdownOpen = false
		}
	}

	private syncAvailableFrontends(loadedChainNames: string[]) {
		this.availableFrontendNames = this.getFrontendNamesForChains(loadedChainNames)

		if (!this.hasCustomizedFrontendSelection) {
			this.selectedFrontendNames = [...this.availableFrontendNames]
		} else {
			const availableFrontendSet = new Set(this.availableFrontendNames)
			this.selectedFrontendNames = this.selectedFrontendNames.filter(frontendName => availableFrontendSet.has(frontendName))
		}

		this.selectedFrontendNames$.next([...this.selectedFrontendNames])
	}

	private scrollDropdownList(event: WheelEvent, list: HTMLElement | null) {
		event.stopPropagation()

		if (!list) {
			event.preventDefault()
			return
		}

		const scrollable = list.scrollHeight > list.clientHeight
		if (!scrollable) {
			event.preventDefault()
			return
		}

		const delta =
			event.deltaMode === WheelEvent.DOM_DELTA_LINE
				? event.deltaY * 16
				: event.deltaMode === WheelEvent.DOM_DELTA_PAGE
					? event.deltaY * list.clientHeight
					: event.deltaY

		event.preventDefault()
		list.scrollTop += delta
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
