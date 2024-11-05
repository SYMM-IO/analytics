import { DailyHistory, MonthlyHistory, SolverDailyHistory, TotalHistory, WeeklyHistory } from "../models"
import BigNumber from "bignumber.js"
import { Affiliate } from "../../environments/environment-interface"

type HistoryType = DailyHistory | SolverDailyHistory | TotalHistory | WeeklyHistory | MonthlyHistory

function genericAggregateHistories<T extends HistoryType>(histories: T[], keys: (keyof T)[], avgKeys: (keyof T)[]): T {
	let base = new (histories[0].constructor as { new (): T })()
	base.id = histories[0].id
	base.accountSource = histories[0].accountSource
	const sumAccumulator = histories.reduce((accumulator: T, current: T, _: number) => {
		for (const key of keys) {
			let value = current[key] as BigNumber
			const accValue = (accumulator[key] as BigNumber) || BigNumber(0)
			accumulator[key] = accValue.plus(value as BigNumber) as any
		}
		return accumulator
	}, base)

	// Calculate averages for avgKeys
	for (const key of avgKeys) {
		if (sumAccumulator[key] != undefined) {
			sumAccumulator[key] = (sumAccumulator[key]! as any).div(histories.length) as any
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
	const avgKeys: (keyof DailyHistory)[] = ["averagePositionSize"]
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
	const avgKeys: (keyof SolverDailyHistory)[] = ["averagePositionSize"]
	return genericAggregateHistories(histories, keys, avgKeys)
}

export function aggregateTotalHistories(histories: TotalHistory[]): TotalHistory {
	const keys: (keyof TotalHistory)[] = ["quotesCount", "tradeVolume", "deposit", "users", "accounts", "platformFee", "openInterest"]
	const avgKeys: (keyof TotalHistory)[] = []
	return genericAggregateHistories(histories, keys, avgKeys)
}

export function aggregateWeeklyHistories(histories: WeeklyHistory[]): WeeklyHistory {
	const keys: (keyof WeeklyHistory)[] = ["activeUsers"]
	const avgKeys: (keyof WeeklyHistory)[] = []
	return genericAggregateHistories(histories, keys, avgKeys)
}

export function aggregateMonthlyHistories(histories: MonthlyHistory[]): MonthlyHistory {
	const keys: (keyof MonthlyHistory)[] = ["activeUsers"]
	const avgKeys: (keyof MonthlyHistory)[] = []
	return genericAggregateHistories(histories, keys, avgKeys)
}
