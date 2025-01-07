import { Component, EventEmitter, Input, OnInit, Output } from "@angular/core"
import { GroupedHistory } from "../groupedHistory"
import { EnvironmentService } from "../services/enviroment.service"
import { ApolloManagerService } from "../services/apollo-manager-service"
import { GraphQlClient, QueryConfig } from "../services/graphql-client"
import { EnvironmentInterface } from "../../environments/environment-interface"
import { LoadingService } from "../services/Loading.service"
import { catchError, Observable, shareReplay, switchMap, zip } from "rxjs"
import { map, tap } from "rxjs/operators"
import { TuiAlertService } from "@taiga-ui/core"
import { MonthlyHistory, WeeklyHistory } from "../models"
import { aggregateMonthlyHistories, aggregateWeeklyHistories } from "../utils/aggregate-utils"
import BigNumber from "bignumber.js"
import { aggregateHistories, collectAllDates, justifyHistoriesToDates } from "../utils/common-utils"

function deepCopy<T>(obj: T): T {
	if (obj === null || typeof obj !== "object") return obj

	if (Array.isArray(obj)) {
		return obj.map(item => deepCopy(item)) as unknown as T
	}

	const copy = {} as T
	for (const key in obj) {
		if (obj.hasOwnProperty(key)) {
			;(copy as any)[key] = deepCopy((obj as any)[key])
		}
	}
	return copy
}

@Component({
	selector: "app-affiliates-charts",
	templateUrl: "./affiliates-charts.component.html",
	styleUrls: ["./affiliates-charts.component.scss"],
})
export class AffiliatesChartsComponent implements OnInit {
	@Input() groupedHistories!: Observable<GroupedHistory[]>
	@Input() decimalsMap!: Map<string, number>
	@Output() totalMonthlyHistory = new EventEmitter<MonthlyHistory>()

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
		const flatAffiliates = this.environments.map((env: EnvironmentInterface) => env.affiliates!).flat()

		this.groupedHistories = this.groupedHistories.pipe(
			switchMap(value => {
				return zip(
					this.environments
						.map((env: EnvironmentInterface) => {
							return env.affiliates!.map(aff => {
								return {
									affiliate: aff,
									env: env,
									graphQlClient: new GraphQlClient(this.apolloService.getClient(env.subgraphUrl!)!, this.loadingService),
								}
							})
						})
						.flat()
						.map(context => {
							const configs: QueryConfig<any>[] = [
								{
									method: "monthlyHistories",
									fields: ["id", "timestamp", "tradeVolume", "activeUsers", "accountSource"],
									first: 1000,
									orderBy: "timestamp",
									conditions: [
										{
											field: "accountSource",
											operator: "contains",
											value: `"${context.affiliate.address!.toLowerCase()}"`,
										},
									],
									createFunction: (obj: any) => MonthlyHistory.fromRawObject(obj).applyDecimals(context.env.collateralDecimal!),
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
											value: `"${context.affiliate.address!.toLowerCase()}"`,
										},
									],
									createFunction: (obj: any) => WeeklyHistory.fromRawObject(obj).applyDecimals(context.env.collateralDecimal!),
								},
							]

							const startPaginationFields = {
								monthlyHistories: "0",
								weeklyHistories: "0",
							}

							return context.graphQlClient.loadAll(configs, 1000, startPaginationFields).pipe(
								map(result => {
									return [result["monthlyHistories"] || [], result["weeklyHistories"] || []]
								}),
							)
						}),
				).pipe(
					catchError(err => {
						this.loadingService.setLoading(false)
						this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
						throw err
					}),
					map(val => {
						let newValue: GroupedHistory[] = value.map(groupedHistory => ({
							index: { ...groupedHistory.index },
							dailyHistories: groupedHistory.dailyHistories.map(dh => ({ ...dh })),
							weeklyHistories: groupedHistory.weeklyHistories.map(wh => ({ ...wh })),
							monthlyHistories: groupedHistory.monthlyHistories.map(mh => ({ ...mh })),
						})) as any
						for (let i = 0; i < val.length; i++) {
							const affiliateData = val[i]
							const affiliate = flatAffiliates[i]
							const monthlyHistories: MonthlyHistory[] = affiliateData[0]
							const weeklyHistories: WeeklyHistory[] = affiliateData[1]
							newValue.push({
								dailyHistories: [],
								monthlyHistories: monthlyHistories,
								weeklyHistories: weeklyHistories,
								index: affiliate,
							})
						}
						return newValue!
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
				)
			}),
			tap((affiliateHistories: GroupedHistory[]) => {
				// Collect each affiliate's second-last monthly history
				const lastMonthEntries = affiliateHistories
					.map(ah => {
						const m = ah.monthlyHistories
						// only grab it if there's at least 2 months
						return m.length >= 2 ? m[m.length - 2] : null
					})
					.filter(Boolean) as MonthlyHistory[]

				// Aggregate them
				const aggregatedLastMonth = aggregateMonthlyHistories(lastMonthEntries)

				// Emit the result
				this.totalMonthlyHistory.emit(aggregatedLastMonth)
			}),
			shareReplay(1),
		)
	}

	moneyValueFormatter(x: any) {
		return BigNumber(x).toFormat(3)
	}
}
