import {Pipe, PipeTransform} from '@angular/core'
import {BigNumber} from 'bignumber.js'

@Pipe({
	name: 'bigNumberFormat',
})
export class BigNumberFormatPipe implements PipeTransform {

	transform(value: BigNumber | undefined, decimals: number = 18, fixedDecimalPlaces: number = 2): string {
		if (!value)
			return '-'
		let adjustedValue = (value.gte(0) ? value : value.negated()).dividedBy(new BigNumber(10).pow(decimals))
		if (value.lt(0))
			adjustedValue = adjustedValue.negated()
		let formattedValue = adjustedValue.toFixed(fixedDecimalPlaces)
		return formattedValue.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
	}
}
