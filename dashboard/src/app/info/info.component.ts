import {LoadingService} from "../services/Loading.service"
import {Component, Input} from "@angular/core"
import BigNumber from "bignumber.js"

@Component({
    selector: "app-info",
    templateUrl: "./info.component.html",
    styleUrls: ["./info.component.scss"],
})
export class InfoComponent {
    @Input() title?: string
    @Input() totalValue?: BigNumber
    @Input() todayValue?: BigNumber
    @Input() lastDayValue?: BigNumber
    @Input() formatMoney: boolean = false
    @Input() decimals: number = 18

    constructor(readonly loadingService: LoadingService) {

    }

    unDecimal(value: BigNumber): BigNumber {
        return value.div(BigNumber(10).pow(this.decimals))
    }


    formatValue(value: BigNumber): string {
        if (this.formatMoney)
            return "$" + this.unDecimal(value).toFormat(3)
        else
            return value.toFormat()
    }
}
