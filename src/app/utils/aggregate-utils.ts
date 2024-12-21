import BigNumber from "bignumber.js"
import { DailyHistory, MonthlyHistory, SolverDailyHistory, TotalHistory, WeeklyHistory } from "../models"

type HistoryType = DailyHistory | SolverDailyHistory | TotalHistory | WeeklyHistory | MonthlyHistory

function genericAggregateHistories<T extends HistoryType>(
	histories: T[],
	keys: (keyof T)[],
	avgKeys: [keyof T, keyof T][], // [valueKey, weightKey] pairs
): T {
	let base = new (histories[0].constructor as { new (): T })()
	base.id = histories[0].id
	base.accountSource = histories[0].accountSource

	// First pass: sum up all regular keys
	const sumAccumulator = histories.reduce((accumulator: T, current: T, _: number) => {
		for (const key of keys) {
			let value = current[key] as BigNumber
			const accValue = (accumulator[key] as BigNumber) || BigNumber(0)
			accumulator[key] = accValue.plus(value as BigNumber) as any
		}
		return accumulator
	}, base)

	// Calculate weighted averages for avgKeys
	for (const [valueKey, weightKey] of avgKeys) {
		if (sumAccumulator[valueKey] != undefined) {
			// Calculate weighted sum and total weight
			const { weightedSum, totalWeight } = histories.reduce(
				(acc, current) => {
					const value = current[valueKey] as BigNumber
					const weight = current[weightKey] as BigNumber
					return {
						weightedSum: acc.weightedSum.plus(value.times(weight)),
						totalWeight: acc.totalWeight.plus(weight),
					}
				},
				{
					weightedSum: BigNumber(0),
					totalWeight: BigNumber(0),
				},
			)

			// Compute weighted average
			sumAccumulator[valueKey] = totalWeight.isZero() ? BigNumber(0) : (weightedSum.div(totalWeight) as any)
		}
	}

	return sumAccumulator
}
export function aggregateDailyHistories(histories: DailyHistory[]): DailyHistory {
	const keys: (keyof DailyHistory)[] = [
		"quotesCount",
		"tradeVolume",
		"liquidateTradeVolume",
		"averagePositionSize",
		"deposit",
		"withdraw",
		"allocate",
		"deallocate",
		"activeUsers",
		"newUsers",
		"newAccounts",
		"platformFee",
		"openInterest",
	]
	const avgKeys: [keyof DailyHistory, keyof DailyHistory][] = [["averagePositionSize", "quotesCount"]]
	return genericAggregateHistories(histories, keys, avgKeys)
}

export function aggregateSolverDailyHistories(histories: SolverDailyHistory[]): SolverDailyHistory {
	const keys: (keyof SolverDailyHistory)[] = [
		"tradeVolume",
		"averagePositionSize",
		"positionsCount",
		"fundingPaid",
		"fundingReceived",
		"openInterest",
	]
	const avgKeys: [keyof SolverDailyHistory, keyof SolverDailyHistory][] = [["averagePositionSize", "positionsCount"]]
	return genericAggregateHistories(histories, keys, avgKeys)
}

export function aggregateTotalHistories(histories: TotalHistory[]): TotalHistory {
	const keys: (keyof TotalHistory)[] = ["quotesCount", "tradeVolume", "deposit", "users", "accounts", "platformFee", "openInterest"]
	const avgKeys: [keyof TotalHistory, keyof TotalHistory][] = []
	return genericAggregateHistories(histories, keys, avgKeys)
}

export function aggregateWeeklyHistories(histories: WeeklyHistory[]): WeeklyHistory {
	const keys: (keyof WeeklyHistory)[] = ["activeUsers"]
	const avgKeys: [keyof WeeklyHistory, keyof WeeklyHistory][] = []
	return genericAggregateHistories(histories, keys, avgKeys)
}

export function aggregateMonthlyHistories(histories: MonthlyHistory[]): MonthlyHistory {
	const keys: (keyof MonthlyHistory)[] = ["activeUsers"]
	const avgKeys: [keyof MonthlyHistory, keyof MonthlyHistory][] = []
	return genericAggregateHistories(histories, keys, avgKeys)
}
