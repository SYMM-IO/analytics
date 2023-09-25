import {Component, OnInit} from '@angular/core';
import {catchError, combineLatest, Observable, shareReplay, tap} from "rxjs";
import {DailyHistory} from "../services/graph-models";
import BigNumber from "bignumber.js";
import {GraphQlClient} from "../services/graphql-client";
import {MessageService} from "primeng/api";
import {LoadingService} from "../services/Loading.service";
import {EnvironmentService} from "../services/enviroment.service";
import {ApolloManagerService} from "../services/apollo-manager-service";
import {SubEnvironmentInterface} from "../../environments/environment-interface";
import {map} from "rxjs/operators";
import {aggregateDailyHistories} from "../utils";

@Component({
	selector: 'app-aggregate-home',
	templateUrl: './aggregate-home.component.html',
	styleUrls: ['./aggregate-home.component.scss']
})
export class AggregateHomeComponent implements OnInit {
	dailyHistories?: Observable<DailyHistory[][]>;
	totalVolume?: BigNumber;
	totalUsers?: BigNumber;
	totalAccounts?: BigNumber;
	totalQuotes?: BigNumber;
	totalDeposits?: BigNumber;
	todayHistory?: DailyHistory;
	lastDayHistory?: DailyHistory;
	environments: SubEnvironmentInterface[];

	constructor(
		private messageService: MessageService,
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		readonly apolloService: ApolloManagerService
	) {
		this.environments = environmentService.getValue("environments");
	}

	ngOnInit(): void {
		this.dailyHistories = combineLatest(
			this.environments
				.map((env: SubEnvironmentInterface) => {
					return {
						env: env,
						graphQlClient: new GraphQlClient(this.apolloService.getClient(env.subgraphUrl!)!, this.loadingService)
					}
				})
				.map(context => {
					return context.graphQlClient
						.loadAllWithInterval<DailyHistory>(
							"dailyHistories",
							[
								"withdraw",
								"tradeVolume",
								"quotesCount",
								"newUsers",
								"activeUsers",
								"newAccounts",
								"id",
								"deallocate",
								"allocate",
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
								value: `"${context.env.accountSource}"`
							}],
							context.env.fromTimestamp,
						)
				})
		).pipe(
			catchError((err) => {
				this.loadingService.setLoading(false);
				this.messageService.add({
					severity: "error",
					summary: "Error loading data from subgraph",
					detail: err.message,
				});
				throw err;
			}),
			shareReplay(1),
			map((envHistories: DailyHistory[][]) => {
				let all_dates = new Set<number>()
				for (const envHistory of envHistories)
					for (const history of envHistory)
						all_dates.add(DailyHistory.getTime(history)!)
				let justifiedDailyHistories: DailyHistory[][] = [];
				for (const envHistory of envHistories)
					justifiedDailyHistories.push(this.justifyHistoriesToDates(envHistory, all_dates))
				return justifiedDailyHistories;
			}),
			tap({
				next: (envHistories: DailyHistory[][]) => {
					this.totalVolume = this.aggregateFieldFromNestedList(envHistories, "tradeVolume");
					this.totalUsers = this.aggregateFieldFromNestedList(envHistories, "newUsers");
					this.totalAccounts = this.aggregateFieldFromNestedList(envHistories, "newAccounts");
					this.totalQuotes = this.aggregateFieldFromNestedList(envHistories, "quotesCount");
					this.totalDeposits = this.aggregateFieldFromNestedList(envHistories, "deposit");
					this.todayHistory = aggregateDailyHistories(envHistories.map(ls => ls[ls.length - 1]));
					this.lastDayHistory = aggregateDailyHistories(envHistories.map(ls => ls[ls.length - 2]));
				},
			})
		);
	}

	private justifyHistoriesToDates(histories: DailyHistory[], all_dates: Set<number>): DailyHistory[] {
		let mapped_data = new Map<number, DailyHistory>()
		for (const dh of histories)
			mapped_data.set(DailyHistory.getTime(dh)!, dh);
		const sortedDates = Array.from(all_dates).sort();
		let data: DailyHistory[] = [];
		for (const date of sortedDates)
			data.push(mapped_data.has(date) ? mapped_data.get(date)! : DailyHistory.emtpyOne(date.toString()))
		return data
	}

	private aggregateFieldFromNestedList<T>(nestedList: T[][], fieldName: keyof T): BigNumber {
		return nestedList.reduce((accumulator: BigNumber, list: T[]) => {
			const sumForThisList = list.reduce((innerAccumulator: BigNumber, item: T) => {
				const value: any = item[fieldName];
				if (value)
					return innerAccumulator.plus(value);
				return innerAccumulator;
			}, new BigNumber(0));
			return accumulator.plus(sumForThisList);
		}, new BigNumber(0));
	}

	moneyValueFormatter(x: any) {
		return BigNumber(x).toFormat(3);
	}
}
