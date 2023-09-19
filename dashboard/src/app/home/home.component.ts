import { LoadingService } from "../services/Loading.service";
import { Component, OnInit } from "@angular/core";
import { GraphQlClient } from "../services/graphql-client";
import { catchError, Observable, shareReplay, tap } from "rxjs";
import { DailyHistory } from "../services/graph-models";
import BigNumber from "bignumber.js";
import { MessageService } from "primeng/api";
import { EnvironmentService } from "../services/enviroment.service";

@Component({
    selector: "app-home",
    templateUrl: "./home.component.html",
    styleUrls: ["./home.component.scss"],
})
export class HomeComponent implements OnInit {
    dailyHistories?: Observable<DailyHistory[]>;
    totalVolume?: BigNumber;
    totalUsers?: BigNumber;
    totalAccounts?: BigNumber;
    totalQuotes?: BigNumber;
    totalDeposits?: BigNumber;
    todayHistory?: DailyHistory;
    lastDayHistory?: DailyHistory;
    collateralDecimals: number;
    accountSource: string;
    fromTimestamp: string;

    constructor(
        readonly graphQlClient: GraphQlClient,
        private messageService: MessageService,
        private loadingService: LoadingService,
        readonly environmentService: EnvironmentService
    ) {
        this.collateralDecimals = environmentService.getValue("collateralDecimal");
        this.fromTimestamp = environmentService.getValue("fromTimestamp");
        this.accountSource = environmentService.getValue("accountSource");
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
                    value: `"${this.accountSource}"`
                }],
                this.fromTimestamp,
            )
            .pipe(
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
                tap({
                    next: (histories: DailyHistory[]) => {
                        this.totalVolume = histories.reduce(
                            (acc, curr) => acc.plus(curr.tradeVolume!),
                            BigNumber(0)
                        );
                        this.totalUsers = histories.reduce(
                            (acc, curr) => acc.plus(curr.newUsers!),
                            BigNumber(0)
                        );
                        this.totalAccounts = histories.reduce(
                            (acc, curr) => acc.plus(curr.newAccounts!),
                            BigNumber(0)
                        );
                        this.totalQuotes = histories.reduce(
                            (acc, curr) => acc.plus(curr.quotesCount!),
                            BigNumber(0)
                        );
                        this.totalDeposits = histories.reduce(
                            (acc, curr) => acc.plus(curr.deposit!),
                            BigNumber(0)
                        );
                        this.todayHistory = histories[histories.length - 1];
                        this.lastDayHistory = histories[histories.length - 2];
                    },
                })
            );
    }
}
