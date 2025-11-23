import { ChangeDetectorRef, Component, Inject, OnInit } from "@angular/core"
import { catchError, Observable, shareReplay, tap, zip } from "rxjs"
import { map } from "rxjs/operators"
import { GraphQlClient, QueryConfig } from "../services/graphql-client"
import { LoadingService } from "../services/Loading.service"
import { EnvironmentService } from "../services/enviroment.service"
import { EnvironmentInterface } from "../../environments/environment-interface"
import { TuiAlertService } from "@taiga-ui/core"
import { DailyHistory, TotalHistory } from "../models"
import { aggregateDailyHistories, aggregateTotalHistories } from "../utils/aggregate-utils"
import { GroupedHistory } from "../groupedHistory"
import { aggregateHistories, collectAllDates, justifyHistoriesToDates } from "../utils/common-utils"
import BigNumber from "bignumber.js"

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
	constructor(
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		@Inject(TuiAlertService) protected readonly alert: TuiAlertService,
		private cdr: ChangeDetectorRef,
	) {
		this.environments = environmentService.getValue("environments")
		for (const env of this.environments)
			for (const affiliate of env.affiliates!) this.decimalsMap.set(affiliate.address!.toLowerCase(), env.collateralDecimal!)
	}

	ngOnInit(): void {
		const flatAffiliates = this.environments.map((env: EnvironmentInterface) => env.affiliates!).flat()

		this.groupedHistories = zip(
			this.environments
				.map((env: EnvironmentInterface) => {
					return env.affiliates!.map(aff => {
						return {
							affiliate: aff,
							env: env,
							graphQlClient: new GraphQlClient(env.subgraphUrl!, this.loadingService),
						}
					})
				})
				.flat()
				.map(context => {
					let collaterals = context.env.collaterals!.map(c => `\"${c.toLowerCase()}\"`).join(",")
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
							conditions: [
								{
									field: "accountSource",
									operator: "contains",
									value: `"${context.affiliate.address!.toLowerCase()}"`,
								},
							],
							createFunction: (obj: any) => DailyHistory.fromRawObject(obj).applyDecimals(context.env.collateralDecimal!),
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
									value: `"${context.affiliate.address!.toLowerCase()}"`,
								},
								{
									field: "collateral",
									operator: "in",
									value: `[${collaterals}]`,
								},
							],
							createFunction: (obj: any) => TotalHistory.fromRawObject(obj).applyDecimals(context.env.collateralDecimal!),
						},
					]

					const startPaginationFields = {
						dailyHistories: context.affiliate.fromTimestamp || null,
						totalHistories: "0",
					}
					return context.graphQlClient.loadAll(configs, 1000, startPaginationFields).pipe(
						map(result => {
							return [result["dailyHistories"] || [], result["totalHistories"] || []]
						}),
					)
				}),
		).pipe(
			catchError(err => {
				this.loadingService.setLoading(false)
				this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
				throw err
			}),
			tap(value => {
				const totalHistories: TotalHistory[] = value.map(v => v[1][0]).filter(th => th != null)
				this.totalHistory = aggregateTotalHistories(totalHistories)
				this.cdr.markForCheck()
			}),
			map(value => {
				const dailyHistories: DailyHistory[][] = value.map(v => v[0])
				const out: GroupedHistory[] = []

				for (let i = 0; i < dailyHistories.length; i++) {
					const affiliateDailyHistories = dailyHistories[i]
					if (affiliateDailyHistories.length > 0)
						out.push({
							index: flatAffiliates[i],
							dailyHistories: affiliateDailyHistories,
							weeklyHistories: [],
							monthlyHistories: [],
						})
				}
				return out
			}),
			map((groupedHistories: GroupedHistory[]) => {
				groupedHistories.forEach(groupedHistory => {
					groupedHistory.dailyHistories = justifyHistoriesToDates(groupedHistory.dailyHistories, collectAllDates(groupedHistories, "dailyHistories"))
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
				this.todayHistory = aggregateDailyHistories(affiliateHistories.map(a => a.dailyHistories[a.dailyHistories.length - 1]))

				const lastMonthHistoriesPerAffiliate = affiliateHistories.map(a => this.getLastCalendarMonthHistories(a.dailyHistories))

				const allLastMonthHistories = lastMonthHistoriesPerAffiliate.flat()
				this.lastMonthHistory = aggregateDailyHistories(allLastMonthHistories)
				this.cdr.markForCheck()
			}),
			shareReplay(1),
		)
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
