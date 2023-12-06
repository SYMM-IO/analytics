import {Inject, Injectable} from '@angular/core'
import {GraphQlClient} from "../services/graphql-client"
import {catchError, Observable} from "rxjs"
import {ApolloManagerService} from "../services/apollo-manager-service"
import {LoadingService} from "../services/Loading.service"
import {TuiAlertService} from "@taiga-ui/core"

@Injectable({
    providedIn: 'root',
})
export class QuoteService {

    constructor(
        readonly apolloService: ApolloManagerService,
        private loadingService: LoadingService,
        @Inject(TuiAlertService) protected readonly alert: TuiAlertService,
    ) {
    }

    loadQuote(subgraphUrl: string, quoteId: number): Observable<any> {
        let graphQlClient = new GraphQlClient(this.apolloService.getClient(subgraphUrl)!, this.loadingService)
        return graphQlClient
            .load(
                [
                    {
                        method: "quote",
                        createFunction: obj => obj,
                        query: `quote(id: "${quoteId}") {
                                    updateTimestamp
                                    transaction
                                    timestamp
                                    symbolId
                                    quoteStatus
                                    quantity
                                    price
                                    positionType
                                    partyBsWhiteList
                                    partyB
                                    orderType
                                    openPrice
                                    mm
                                    maxInterestRate
                                    marketPrice
                                    liquidatedSide
                                    id
                                    deadline
                                    lf
                                    cva
                                    collateral
                                    closedAmount
                                    blockNumber
                                    avgClosedPrice
                                    account
                                  }`,
                    },
                ],
            )
            .pipe(
                catchError((err) => {
                    this.loadingService.setLoading(false)
                    this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
                    throw err
                }),
            )
    }
}
