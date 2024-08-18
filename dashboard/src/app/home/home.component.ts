import {Component, Inject, OnInit} from '@angular/core'
import {catchError, combineLatest, Observable, of, shareReplay, tap, zip} from "rxjs"
import {DailyHistory, MonthlyHistory, TotalHistory, WeeklyHistory} from "../models"
import BigNumber from "bignumber.js"
import {GraphQlClient} from "../services/graphql-client"
import {LoadingService} from "../services/Loading.service"
import {EnvironmentService} from "../services/enviroment.service"
import {ApolloManagerService} from "../services/apollo-manager-service"
import {EnvironmentInterface, Version} from "../../environments/environment-interface"
import {map} from "rxjs/operators"
import {
	aggregateDailyHistories,
	aggregateMonthlyHistories,
	aggregateTotalHistories,
	aggregateWeeklyHistories
} from "../utils"
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
		this.dailyAffiliateHistories = zip(
			this.environments
				.map((env: EnvironmentInterface) => {
					return env.affiliates!
						.filter(aff => this.singleAffiliateAccountSource == null || aff.accountSource == this.singleAffiliateAccountSource)
						.map(aff => {
							return {
								version: env.version,
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
							context.version == Version.V_0_8_2 ? context.graphQlClient
								.loadAllWithInterval<TotalHistory>(
									"monthlyHistories",
									[
										"id",
										"timestamp",
										"tradeVolume",
										"activeUsers",
										"accountSource",
									],
									"timestamp",
									(obj: any) => MonthlyHistory.fromRawObject(obj),
									[{
										field: "accountSource",
										operator: "contains",
										value: `"${context.affiliate.accountSource}"`,
									}],
									"0",
								) : of([]),
							context.version == Version.V_0_8_2 ? context.graphQlClient
								.loadAllWithInterval<TotalHistory>(
									"weeklyHistories",
									[
										"id",
										"timestamp",
										"tradeVolume",
										"activeUsers",
										"accountSource",
									],
									"timestamp",
									(obj: any) => WeeklyHistory.fromRawObject(obj),
									[{
										field: "accountSource",
										operator: "contains",
										value: `"${context.affiliate.accountSource}"`,
									}],
									"0",
								) : of([]),
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
			map((value) => {
				let affiliateHistories: DailyHistory[][] = value.map(v => v[0])
				let monthlyHistories: MonthlyHistory[][] = value.map(v => v[2])
				let weeklyHistories: WeeklyHistory[][] = value.map(v => v[3])
				let out: AffiliateHistory[] = []
				for (let i = 0; i < affiliateHistories!.length; i++) {
					const affiliateHistory = affiliateHistories![i]
					if (affiliateHistory.length > 0)
						out.push({
							affiliate: flatAffiliates[i],
							histories: affiliateHistory,
							weeklyHistories: weeklyHistories[i],
							monthlyHistories: monthlyHistories[i]
						})
				}
				return out
			}),
			map((affiliateHistories: AffiliateHistory[]) => {
				// For daily histories
				let all_daily_dates = new Set<number>();
				for (const affiliateHistory of affiliateHistories) {
					for (const history of affiliateHistory.histories) {
						all_daily_dates.add(DailyHistory.getTime(history)!);
					}
				}
				for (const affiliateHistory of affiliateHistories) {
					affiliateHistory.histories = this.justifyHistoriesToDates(affiliateHistory.histories, all_daily_dates);
				}

				// For weekly histories
				let all_weekly_dates = new Set<number>();
				for (const affiliateHistory of affiliateHistories) {
					for (const history of affiliateHistory.weeklyHistories) {
						all_weekly_dates.add(WeeklyHistory.getTime(history)!);
					}
				}
				for (const affiliateHistory of affiliateHistories) {
					if (affiliateHistory.weeklyHistories.length > 0)
						affiliateHistory.weeklyHistories = this.justifyHistoriesToDates(affiliateHistory.weeklyHistories, all_weekly_dates);
				}

				// For monthly histories
				let all_monthly_dates = new Set<number>();
				for (const affiliateHistory of affiliateHistories) {
					for (const history of affiliateHistory.monthlyHistories) {
						all_monthly_dates.add(MonthlyHistory.getTime(history)!);
					}
				}
				for (const affiliateHistory of affiliateHistories) {
					if (affiliateHistory.monthlyHistories.length > 0)
						affiliateHistory.monthlyHistories = this.justifyHistoriesToDates(affiliateHistory.monthlyHistories, all_monthly_dates);
				}

				return affiliateHistories;
			}),
			map((affiliateHistories: AffiliateHistory[]) => {
				let map = new Map<string, AffiliateHistory>();
				for (const affiliateHistory of affiliateHistories) {
					const affiliate = affiliateHistory.affiliate.name!;
					if (map.has(affiliate)) {
						let existingHistory = map.get(affiliate)!;
						let aggregated_source = `${affiliateHistory.histories[0]}-${existingHistory.histories[0]}`;

						// Aggregate daily histories
						existingHistory.histories = this.aggregateHistories(
							affiliateHistory.histories,
							existingHistory.histories,
							aggregateDailyHistories
						);

						// Aggregate weekly histories
						existingHistory.weeklyHistories = this.aggregateHistories(
							affiliateHistory.weeklyHistories,
							existingHistory.weeklyHistories,
							aggregateWeeklyHistories
						);

						// Aggregate monthly histories
						existingHistory.monthlyHistories = this.aggregateHistories(
							affiliateHistory.monthlyHistories,
							existingHistory.monthlyHistories,
							aggregateMonthlyHistories
						);

						this.decimalsMap.set(aggregated_source, 18);

						// Update account source for all history types
						[existingHistory.histories, existingHistory.weeklyHistories, existingHistory.monthlyHistories].forEach(histories => {
							histories = histories.map(value => {
								value.accountSource = aggregated_source;
								return value;
							});
						});

						map.set(affiliate, existingHistory);
					} else {
						map.set(affiliate, affiliateHistory);
					}
				}
				return [...map.values()];
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


	private getTimeFromHistory(history: DailyHistory | WeeklyHistory | MonthlyHistory): number {
		if (history instanceof DailyHistory) return DailyHistory.getTime(history)!;
		if (history instanceof WeeklyHistory) return WeeklyHistory.getTime(history)!;
		if (history instanceof MonthlyHistory) return MonthlyHistory.getTime(history)!;
		throw new Error("Unknown history type");
	}

	private createEmptyHistory(date: number, template: DailyHistory | WeeklyHistory | MonthlyHistory): DailyHistory | WeeklyHistory | MonthlyHistory {
		if (template instanceof DailyHistory) return DailyHistory.emptyOne(date.toString(), template.accountSource);
		if (template instanceof WeeklyHistory) return WeeklyHistory.emptyOne(date.toString(), template.accountSource);
		if (template instanceof MonthlyHistory) return MonthlyHistory.emptyOne(date.toString(), template.accountSource);
		throw new Error("Unknown history type");
	}

	private justifyHistoriesToDates<T extends DailyHistory | WeeklyHistory | MonthlyHistory>(
		histories: T[],
		all_dates: Set<number>
	): T[] {
		let mapped_data = new Map<number, T>();
		for (const history of histories) {
			mapped_data.set(this.getTimeFromHistory(history), history);
		}
		const sortedDates = Array.from(all_dates).sort();
		let data: T[] = [];
		for (const date of sortedDates) {
			data.push(mapped_data.has(date)
				? mapped_data.get(date)!
				: this.createEmptyHistory(date, histories[0]) as T
			);
		}
		return data;
	}

	moneyValueFormatter(x: any) {
		return BigNumber(x).toFormat(3)
	}

	// Helper method to aggregate histories
	private aggregateHistories<T>(
		histories1: T[],
		histories2: T[],
		aggregateFunction: (histories: T[], decimalsMap: Map<string, number>) => T
	): T[] {
		let aggregatedHistories: T[] = [];
		for (let i = 0; i < Math.max(histories1.length, histories2.length); i++) {
			let history1 = i < histories1.length ? histories1[i] : null;
			let history2 = i < histories2.length ? histories2[i] : null;
			if (history1 && history2) {
				aggregatedHistories.push(aggregateFunction([history1, history2], this.decimalsMap));
			} else {
				aggregatedHistories.push(history1 || history2!);
			}
		}
		return aggregatedHistories;
	}
}
