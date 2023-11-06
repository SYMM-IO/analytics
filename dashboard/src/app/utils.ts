import {DailyHistory} from "./services/graph-models"
import BigNumber from "bignumber.js"

export function aggregateDailyHistories(histories: DailyHistory[]): DailyHistory {
	const keys = [
		"quotesCount",
		"tradeVolume",
		"deposit",
		"withdraw",
		"allocate",
		"deallocate",
		"activeUsers",
		"newUsers",
		"newAccounts",
		"platformFee",
		"openInterest"
	]
	let base = new DailyHistory()
	base.id = histories[0].id
	return histories.reduce((accumulator: DailyHistory, current: DailyHistory) => {
		for (const key of keys) {
			const accValue = accumulator[key] as BigNumber || BigNumber(0)
			const currValue = current[key] as BigNumber
			accumulator[key] = accValue.plus(currValue)
		}
		return accumulator
	}, base)
}