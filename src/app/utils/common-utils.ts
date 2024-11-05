import { BaseHistory } from "../models"
import { GroupedHistory } from "../groupedHistory"

export function justifyHistoriesToDates<T extends BaseHistory>(histories: T[], all_dates: Set<number>): T[] {
	let mapped_data = new Map<number, T>()
	for (const history of histories) {
		mapped_data.set(BaseHistory.getTime(history)!, history)
	}
	const sortedDates = Array.from(all_dates).sort()
	let data: T[] = []
	for (const date of sortedDates) {
		data.push(mapped_data.has(date) ? mapped_data.get(date)! : (histories[0].emptyOne(date) as T))
	}
	return data
}

export function collectAllDates(
	affiliateHistories: GroupedHistory[],
	property: "dailyHistories" | "weeklyHistories" | "monthlyHistories",
): Set<number> {
	let all_dates = new Set<number>()
	affiliateHistories.forEach(affiliateHistory => {
		affiliateHistory[property].forEach((history: any) => {
			const time = BaseHistory.getTime(history)
			if (time != undefined) all_dates.add(time)
		})
	})
	return all_dates
}

export function aggregateHistories<T>(histories1: T[], histories2: T[], aggregateFunction: (histories: T[]) => T): T[] {
	let aggregatedHistories: T[] = []
	for (let i = 0; i < Math.max(histories1.length, histories2.length); i++) {
		let history1 = i < histories1.length ? histories1[i] : null
		let history2 = i < histories2.length ? histories2[i] : null
		if (history1 && history2) {
			aggregatedHistories.push(aggregateFunction([history1, history2]))
		} else {
			aggregatedHistories.push(history1 || history2!)
		}
	}
	return aggregatedHistories
}
