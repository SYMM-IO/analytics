import { Inject, Injectable } from "@angular/core";
import { Observable } from "rxjs";
import { ApolloManagerService } from "./apollo-manager-service";
import { LoadingService } from "./Loading.service";
import { TuiAlertService } from "@taiga-ui/core";

@Injectable({
	providedIn: "root",
})
export class QuoteService {

	constructor(
		readonly apolloService: ApolloManagerService,
		private loadingService: LoadingService,
		@Inject(TuiAlertService) protected readonly alert: TuiAlertService,
	) {
	}

	loadQuote(subgraphUrl: string, quoteId: number): Observable<any> {
		return new Observable();
		// let graphQlClient = new GraphQlClient(this.apolloService.getClient(subgraphUrl)!, this.loadingService)
		// return graphQlClient
		// 	.load(
		// 		[
		// 			{
		// 				method: "quote",
		// 				createFunction: obj => obj,
		// 				query: `quote(id: "${quoteId}") {
		//                             id
		//                             account
		//                             partyBsWhiteList
		//                             symbolId
		//                             symbolName
		//                             positionType
		//                             orderType
		//                             openOrderType
		//                             price
		//                             marketPrice
		//                             openPrice
		//                             openedPrice
		//                             deadline
		//                             quantity
		//                             cva
		//                             partyAmm
		//                             partyBmm
		//                             lf
		//                             quoteStatus
		//                             blockNumber
		//                             closedAmount
		//                             avgClosedPrice
		//                             partyB
		//                             collateral
		//                             liquidatedSide
		//                             fundingPaid
		//                             fundingReceived
		//                             timestamp
		//                             updateTimestamp
		//                             transaction
		//                           }`,
		// 			},
		// 		],
		// 	)
		// 	.pipe(
		// 		catchError((err) => {
		// 			this.loadingService.setLoading(false)
		// 			this.alert.open("Error loading data from subgraph\n" + err.message).subscribe()
		// 			throw err
		// 		}),
		// 	)
	}
}
