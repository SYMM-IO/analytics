import {Pipe, PipeTransform} from '@angular/core'
import {BigNumber} from 'bignumber.js'

@Pipe({
    name: 'bigNumberFormat',
})
export class BigNumberFormatPipe implements PipeTransform {

    transform(value: BigNumber | undefined, decimals: number = 18, fixedDecimalPlaces: number = 2): string {
        if (!value)
            return '0'
        let adjustedValue = value.dividedBy(new BigNumber(10).pow(decimals))
        let formattedValue = adjustedValue.toFixed(fixedDecimalPlaces)
        return formattedValue.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
    }
}
