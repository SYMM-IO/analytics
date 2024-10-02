import { TuiLet } from "@taiga-ui/cdk";
import { TuiAccordion } from "@taiga-ui/kit";
import {Component, Inject} from '@angular/core'
import {TuiDialogContext, TuiDialogService} from "@taiga-ui/core"
import {POLYMORPHEUS_CONTEXT} from "@taiga-ui/polymorpheus"
import {EnvironmentInterface} from "../../../../environments/environment-interface"
import BigNumber from "bignumber.js"

@Component({
	selector: 'quote-viewer',
	standalone: true,
	imports: [
		TuiLet,
		TuiAccordion,
	],
	templateUrl: './quote-viewer.component.html',
	styleUrl: './quote-viewer.component.scss',
})
export class QuoteViewerComponent {
	quote: any
	positionTypeMap = new Map<number, string>([
		[0, "Long"],
		[1, "Short"],
	])
	orderTypeMap = new Map<number, string>([
		[0, "Limit"],
		[1, "Market"],
	])
	quoteStatusMap = new Map<number, string>([
		[0, "Pending"],
		[1, "Locked"],
		[2, "Cancel Pending"],
		[3, "Canceled"],
		[4, "Opened"],
		[5, "Close Pending"],
		[6, "Cancel Close Pending"],
		[7, "Closed"],
		[8, "Liquidated"],
		[9, "Expired"],
	])
	environment: EnvironmentInterface

	constructor(@Inject(TuiDialogService) private readonly dialogs: TuiDialogService,
				@Inject(POLYMORPHEUS_CONTEXT) readonly context: TuiDialogContext<number, number>) {
		this.quote = (context.data as any)[0]
		this.environment = (context.data as any)[1]
	}

	unDecimal(value: BigNumber, decimals: number): BigNumber {
		return value.div(BigNumber(10).pow(decimals))
	}

	formatValue(value: number, formatMoney: boolean = true, decimals: number = 18): string {
		if (formatMoney)
			return "$" + this.unDecimal(BigNumber(value), decimals).toFormat(3)
		else
			return this.unDecimal(BigNumber(value), decimals).toFormat()
	}
}
