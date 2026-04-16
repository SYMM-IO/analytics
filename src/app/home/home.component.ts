import { ChangeDetectorRef, Component, HostListener, Inject, OnInit } from "@angular/core"
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
	chainDropdownOpen = false
	private readonly selectedChainNames$ = new BehaviorSubject<string[]>([])
	private hasCustomizedChainSelection = false
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

		this.groupedHistories = combineLatest([environmentResults$, this.selectedChainNames$]).pipe(
			map(([environmentResults, selectedChainNames]) => {
				const selectedChainsSet = new Set(selectedChainNames)
				return environmentResults.filter(result => selectedChainsSet.has(result.environmentName))
			}),
			catchError(err => {
				this.loadingService.setLoading(false)
				this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
				throw err
			}),
			tap(environmentResults => {
				const totalHistories: TotalHistory[] = environmentResults.flatMap(result => result.totalHistories).filter(th => th != null)
				this.totalHistory = totalHistories.length > 0 ? aggregateTotalHistories(totalHistories) : undefined
				this.cdr.markForCheck()
			}),
			map(environmentResults => {
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
				return out
			}),
			map((groupedHistories: GroupedHistory[]) => {
				const all_dates = collectAllDates(groupedHistories, "dailyHistories")
				groupedHistories.forEach(groupedHistory => {
					// Aggregate multiple dailyHistories for the same day and accountSource
					let mapped_data = new Map<number, DailyHistory>()
					for (const history of groupedHistory.dailyHistories) {
						const time = BaseHistory.getTime(history)!
						if (mapped_data.has(time)) {
							let lastHistory = mapped_data.get(time)!
							let aggregatedHistory = aggregateDailyHistories([lastHistory, history])
							aggregatedHistory.timestamp = lastHistory.timestamp! >= history.timestamp! ? lastHistory.timestamp : history.timestamp
							mapped_data.set(time, aggregatedHistory)
						} else {
							mapped_data.set(time, history)
						}
					}
					groupedHistory.dailyHistories = justifyHistoriesToDates([...mapped_data.values()], all_dates)
				})
				return groupedHistories
			}),
			map((affiliateHistories: GroupedHistory[]) => {
				// Aggregate histories for affiliates with the same name 
				const map = new Map<string, GroupedHistory>()
				for (const affiliateHistory of affiliateHistories) {
					const affiliate = affiliateHistory.index.name!
					if (map.has(affiliate)) {
						let existingHistory = map.get(affiliate)!
						existingHistory.dailyHistories = aggregateHistories(
							affiliateHistory.dailyHistories,
							existingHistory.dailyHistories,
							aggregateDailyHistories,
						)
						map.set(affiliate, existingHistory)
					} else {
						map.set(affiliate, affiliateHistory)
					}
				}
				return [...map.values()]
			}),
			tap((affiliateHistories: GroupedHistory[]) => {
				const latestHistories = affiliateHistories.map(a => a.dailyHistories[a.dailyHistories.length - 1] as DailyHistory).filter(Boolean)
				this.todayHistory = latestHistories.length > 0 ? aggregateDailyHistories(latestHistories) : undefined

				const lastMonthHistoriesPerAffiliate = affiliateHistories.map(a => this.getLastCalendarMonthHistories(a.dailyHistories))
				const allLastMonthHistories = lastMonthHistoriesPerAffiliate.flat()
				this.lastMonthHistory = allLastMonthHistories.length > 0 ? aggregateDailyHistories(allLastMonthHistories) : undefined
				this.cdr.markForCheck()
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

	toggleChainDropdown() {
		if (this.loadedChainNames.length === 0 && this.ignoredChainNames.length === 0) return
		this.chainDropdownOpen = !this.chainDropdownOpen
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

	@HostListener("document:click", ["$event"])
	onDocumentClick(event: MouseEvent) {
		const target = event.target as HTMLElement
		const dropdownContainer = target.closest(".chain-filter-container")
		if (!dropdownContainer && this.chainDropdownOpen) {
			this.chainDropdownOpen = false
		}
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
