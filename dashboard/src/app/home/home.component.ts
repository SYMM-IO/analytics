import {LoadingService} from "../services/Loading.service"
import {Component, Inject, OnInit} from "@angular/core"
import {GraphQlClient} from "../services/graphql-client"
import {catchError, Observable, shareReplay, tap} from "rxjs"
import {DailyHistory} from "../services/graph-models"
import BigNumber from "bignumber.js"
import {EnvironmentService} from "../services/enviroment.service"
import {ApolloManagerService} from "../services/apollo-manager-service"
import {map} from "rxjs/operators"
import {SubEnvironmentInterface} from "../../environments/environment-interface"
import {TuiAlertService} from "@taiga-ui/core"

@Component({
	selector: "app-home",
	templateUrl: "./home.component.html",
	styleUrls: ["./home.component.scss"],
})
export class HomeComponent implements OnInit {
	dailyHistories?: Observable<DailyHistory[][]>
	totalVolume?: BigNumber
	totalUsers?: BigNumber
	totalAccounts?: BigNumber
	totalQuotes?: BigNumber
	totalDeposits?: BigNumber
	todayHistory?: DailyHistory
	lastDayHistory?: DailyHistory
	graphQlClient: GraphQlClient
	environment: SubEnvironmentInterface

	constructor(
		private loadingService: LoadingService,
		readonly environmentService: EnvironmentService,
		readonly apolloService: ApolloManagerService,
		@Inject(TuiAlertService) protected readonly alert: TuiAlertService,
	) {
		this.environment = environmentService.getValue("environments")[0]
		this.graphQlClient = new GraphQlClient(this.apolloService.getClient(this.environment.subgraphUrl!)!, this.loadingService)
	}

	ngOnInit(): void {
		this.dailyHistories = this.graphQlClient
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
					value: `"${this.environment.accountSource}"`
				}],
				this.environment.fromTimestamp,
			)
			.pipe(
				catchError((err) => {
					this.loadingService.setLoading(false)
					this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
					throw err
				}),
				shareReplay(1),
				tap({
					next: (histories: DailyHistory[]) => {
						this.totalVolume = histories.reduce(
							(acc, curr) => acc.plus(curr.tradeVolume!),
							BigNumber(0)
						)
						this.totalUsers = histories.reduce(
							(acc, curr) => acc.plus(curr.newUsers!),
							BigNumber(0)
						)
						this.totalAccounts = histories.reduce(
							(acc, curr) => acc.plus(curr.newAccounts!),
							BigNumber(0)
						)
						this.totalQuotes = histories.reduce(
							(acc, curr) => acc.plus(curr.quotesCount!),
							BigNumber(0)
						)
						this.totalDeposits = histories.reduce(
							(acc, curr) => acc.plus(curr.deposit!),
							BigNumber(0)
						)
						this.todayHistory = histories[histories.length - 1]
						this.lastDayHistory = histories[histories.length - 2]
					},
				}),
				map(value => [value]),
			)
	}

	moneyValueFormatter(x: any) {
		return BigNumber(x).toFormat(3)
	}
}
