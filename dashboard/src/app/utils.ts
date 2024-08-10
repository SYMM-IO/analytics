import {DailyHistory, MonthlyHistory, TotalHistory, WeeklyHistory} from "./models"
import BigNumber from "bignumber.js"
import {Affiliate} from "../environments/environment-interface"

export function aggregateDailyHistories(histories: DailyHistory[], decimalsMap: Map<string, number> | undefined = undefined): DailyHistory {
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
		"openInterest",
	]
	const withDecimalsKeys = [
		"deposit",
		"withdraw",
	]
	let base = new DailyHistory()
	base.id = histories[0].id
	base.accountSource = histories[0].accountSource
	return histories.reduce((accumulator: DailyHistory, current: DailyHistory) => {
		for (const key of keys) {
			let value = current[key] as BigNumber
			if (decimalsMap != null && withDecimalsKeys.indexOf(key) >= 0) {
				const accountSource = current.accountSource!
				const decimals = decimalsMap.get(accountSource)!
				value = BigNumber(value!).times(BigNumber(10).pow(18 - decimals))
			}
			const accValue = accumulator[key] as BigNumber || BigNumber(0)
			accumulator[key] = accValue.plus(value as BigNumber)
		}
		return accumulator
	}, base)
}

export function aggregateTotalHistories(histories: TotalHistory[], decimalsMap: Map<string, number> | undefined = undefined, flatAffiliates: Affiliate[]): TotalHistory {
	const keys = [
		"quotesCount",
		"tradeVolume",
		"deposit",
		"users",
		"accounts",
		"platformFee",
		"openInterest",
	]
	const withDecimalsKeys = [
		"deposit",
	]
	let base = new TotalHistory()
	base.id = histories[0].id
	return histories.reduce((accumulator: TotalHistory, current: TotalHistory, currentIndex) => {
		if (current == null)
			return accumulator
		for (const key of keys) {
			let value = current[key] as BigNumber
			if (decimalsMap != null && withDecimalsKeys.indexOf(key) >= 0) {
				const accountSource = current.accountSource!
				const decimals = decimalsMap.get(accountSource)!
				let depositDiff = flatAffiliates[currentIndex].depositDiff
				if (depositDiff != null)
					value = value.minus(depositDiff)
				value = BigNumber(value!).times(BigNumber(10).pow(18 - decimals))
			}
			const accValue = accumulator[key] as BigNumber || BigNumber(0)
			accumulator[key] = accValue.plus(value as BigNumber)
		}
		return accumulator
	}, base)
}

export function aggregateWeeklyHistories(histories: WeeklyHistory[], decimalsMap: Map<string, number> | undefined = undefined): WeeklyHistory {
	const keys = [
		"tradeVolume",
		"activeUsers",
	];
	const withDecimalsKeys = [
		"tradeVolume",
	];
	let base = new WeeklyHistory();
	base.id = histories[0].id;
	base.accountSource = histories[0].accountSource;
	return histories.reduce((accumulator: WeeklyHistory, current: WeeklyHistory) => {
		for (const key of keys) {
			let value = current[key] as BigNumber;
			if (decimalsMap != null && withDecimalsKeys.indexOf(key) >= 0) {
				const accountSource = current.accountSource!;
				const decimals = decimalsMap.get(accountSource)!;
				value = BigNumber(value!).times(BigNumber(10).pow(18 - decimals));
			}
			const accValue = accumulator[key] as BigNumber || BigNumber(0);
			accumulator[key] = accValue.plus(value as BigNumber);
		}
		return accumulator;
	}, base);
}

export function aggregateMonthlyHistories(histories: MonthlyHistory[], decimalsMap: Map<string, number> | undefined = undefined): MonthlyHistory {
	const keys = [
		"tradeVolume",
		"activeUsers",
	];
	const withDecimalsKeys = [
		"tradeVolume",
	];
	let base = new MonthlyHistory();
	base.id = histories[0].id;
	base.accountSource = histories[0].accountSource;
	return histories.reduce((accumulator: MonthlyHistory, current: MonthlyHistory) => {
		for (const key of keys) {
			let value = current[key] as BigNumber;
			if (decimalsMap != null && withDecimalsKeys.indexOf(key) >= 0) {
				const accountSource = current.accountSource!;
				const decimals = decimalsMap.get(accountSource)!;
				value = BigNumber(value!).times(BigNumber(10).pow(18 - decimals));
			}
			const accValue = accumulator[key] as BigNumber || BigNumber(0);
			accumulator[key] = accValue.plus(value as BigNumber);
		}
		return accumulator;
	}, base);
}