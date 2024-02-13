import {Component, Inject, OnInit} from '@angular/core'
import {catchError, combineLatest, Observable, shareReplay, tap} from "rxjs"
import {DailyHistory, TotalHistory} from "../models"
import BigNumber from "bignumber.js"
import {GraphQlClient} from "../services/graphql-client"
import {LoadingService} from "../services/Loading.service"
import {EnvironmentService} from "../services/enviroment.service"
import {ApolloManagerService} from "../services/apollo-manager-service"
import {EnvironmentInterface} from "../../environments/environment-interface"
import {map} from "rxjs/operators"
import {aggregateDailyHistories, aggregateTotalHistories} from "../utils"
import {TuiAlertService} from "@taiga-ui/core"
import {AffiliateHistory} from "../affiliate.history"

@Component({
	selector: 'app-aggregate-home',
	templateUrl: './home.component.html',
	styleUrls: ['./home.component.scss'],
})
export class HomeComponent implements OnInit {
	dailyAffiliateHistories?: Observable<AffiliateHistory[]>
	totalHistory?: TotalHistory
	todayHistory?: DailyHistory
	lastDayHistory?: DailyHistory
	environments: EnvironmentInterface[]
	decimalsMap = new Map<string, number>()
	singleAffiliateAccountSource: string

	constructor(
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		readonly apolloService: ApolloManagerService,
		@Inject(TuiAlertService) protected readonly alert: TuiAlertService,
	) {
		this.environments = environmentService.getValue("environments")
		for (const env of this.environments)
			for (const affiliate of env.affiliates!)
				this.decimalsMap.set(affiliate.accountSource!.toLowerCase(), env.collateralDecimal!)
		this.singleAffiliateAccountSource = this.environmentService.getValue("singleAffiliateAccountSource")
	}

	ngOnInit(): void {
		const flatAffiliates = this.environments
			.map((env: EnvironmentInterface) => env.affiliates!)
			.flat()
			.filter(aff => this.singleAffiliateAccountSource == null || aff.accountSource == this.singleAffiliateAccountSource)
		this.dailyAffiliateHistories = combineLatest(
			this.environments
				.map((env: EnvironmentInterface) => {
					return env.affiliates!
						.filter(aff => this.singleAffiliateAccountSource == null || aff.accountSource == this.singleAffiliateAccountSource)
						.map(aff => {
							return {
								affiliate: aff,
								graphQlClient: new GraphQlClient(this.apolloService.getClient(env.subgraphUrl!)!, this.loadingService),
							}
						})
				})
				.flat()
				.map(context => {
					return combineLatest(
						[
							context.graphQlClient
								.loadAllWithInterval<DailyHistory>(
									"dailyHistories",
									[
										"id",
										"tradeVolume",
										"quotesCount",
										"newUsers",
										"activeUsers",
										"newAccounts",
										"deposit",
										"platformFee",
										"openInterest",
										"accountSource",
									],
									"timestamp",
									(obj: any) => DailyHistory.fromRawObject(obj),
									[{
										field: "accountSource",
										operator: "contains",
										value: `"${context.affiliate.accountSource}"`,
									}],
									context.affiliate.fromTimestamp,
								),
							context.graphQlClient
								.loadAllWithInterval<TotalHistory>(
									"totalHistories",
									[
										"id",
										"users",
										"accounts",
										"deposit",
										"tradeVolume",
										"quotesCount",
										"accountSource",
										"timestamp",
									],
									"timestamp",
									(obj: any) => TotalHistory.fromRawObject(obj),
									[{
										field: "accountSource",
										operator: "contains",
										value: `"${context.affiliate.accountSource}"`,
									}],
									"0",
								),
						],
					)
				}),
		).pipe(
			catchError((err) => {
				this.loadingService.setLoading(false)
				this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
				throw err
			}),
			tap(value => {
				let totalHistories = value.map(value1 => value1[1]).map(value1 => value1[0])
				this.totalHistory = aggregateTotalHistories(totalHistories, this.decimalsMap, flatAffiliates)
			}),
			map(value => {
				return value.map(value1 => value1[0])
			}),
			map((affiliatesHistories: DailyHistory[][]) => {
				let out: AffiliateHistory[] = []
				for (let i = 0; i < affiliatesHistories.length; i++) {
					const affiliateHistory = affiliatesHistories[i]
					out.push({
						affiliate: flatAffiliates[i],
						histories: affiliateHistory,
					})
				}
				return out
			}),
			map((affiliateHistories: AffiliateHistory[]) => {
				let all_dates = new Set<number>()
				for (const affiliateHistory of affiliateHistories)
					for (const history of affiliateHistory.histories)
						all_dates.add(DailyHistory.getTime(history)!)
				for (const affiliateHistory of affiliateHistories)
					affiliateHistory.histories = this.justifyHistoriesToDates(affiliateHistory.histories, all_dates)
				return affiliateHistories
			}),
			map((affiliateHistories: AffiliateHistory[]) => {
				let map = new Map<string, AffiliateHistory>()
				for (const affiliateHistory of affiliateHistories) {
					const affiliate = affiliateHistory.affiliate.name!
					if (map.has(affiliate)) {
						for (let i = 0; i < affiliateHistory.histories.length; i++) {
							map.get(affiliate)!.histories[i] = aggregateDailyHistories([
								affiliateHistory.histories[i], map.get(affiliate)!.histories[i],
							], this.decimalsMap)
						}
					} else {
						map.set(affiliate, affiliateHistory)
					}
				}
				return [...map.values()]
			}),
			tap({
				next: (affiliateHistories: AffiliateHistory[]) => {
					this.todayHistory = aggregateDailyHistories(affiliateHistories.map(a => {
						return a.histories[a.histories.length - 1]
					}))
					this.lastDayHistory = aggregateDailyHistories(affiliateHistories.map(a => {
						return a.histories[a.histories.length - 2]
					}))
				},
			}),
			shareReplay(1),
		)
	}

	private justifyHistoriesToDates(histories: DailyHistory[], all_dates: Set<number>): DailyHistory[] {
		let mapped_data = new Map<number, DailyHistory>()
		for (const dh of histories)
			mapped_data.set(DailyHistory.getTime(dh)!, dh)
		const sortedDates = Array.from(all_dates).sort()
		let data: DailyHistory[] = []
		for (const date of sortedDates)
			data.push(mapped_data.has(date) ? mapped_data.get(date)! : DailyHistory.emtpyOne(date.toString(), histories[0].accountSource))
		return data
	}

	moneyValueFormatter(x: any) {
		return BigNumber(x).toFormat(3)
	}
}
