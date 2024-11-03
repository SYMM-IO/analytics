import BigNumber from "bignumber.js"

function assignBigNumberProperties(target: any, source: any, properties: string[]) {
	for (const prop of properties) {
		target[prop] = BigNumber(source[prop])
	}
}

function assignZeroBigNumberProperties(target: any, properties: string[]) {
	for (const prop of properties) {
		target[prop] = BigNumber(0)
	}
}

export abstract class BaseHistory {
	id?: string
	accountSource?: string

	public static getTime(dh: BaseHistory): number | null {
		if (dh.id != null) return Number(dh.id.split("_")[0])
		return null
	}

	public abstract emptyOne(timestamp: number): BaseHistory

	public abstract applyDecimals(decimals: number, properties: string[]): BaseHistory

	protected doApplyDecimals(decimals: number, properties: string[]): BaseHistory {
		for (const property of properties) {
			;(this as any)[property] = BigNumber((this as any)[property]!).times(BigNumber(10).pow(18 - decimals))
		}
		return this
	}
}

export class DailyHistory extends BaseHistory {
	quotesCount?: BigNumber
	tradeVolume?: BigNumber
	liquidateTradeVolume?: BigNumber
	averagePositionSize?: BigNumber
	deposit?: BigNumber
	withdraw?: BigNumber
	allocate?: BigNumber
	deallocate?: BigNumber
	activeUsers?: BigNumber
	newUsers?: BigNumber
	newAccounts?: BigNumber
	platformFee?: BigNumber
	openInterest?: BigNumber

	static propertyList = [
		"quotesCount",
		"tradeVolume",
		"liquidateTradeVolume",
		"averagePositionSize",
		"deposit",
		"withdraw",
		"allocate",
		"deallocate",
		"newUsers",
		"activeUsers",
		"newAccounts",
		"platformFee",
		"openInterest",
	]

	static withDecimalsProperties = ["deposit", "withdraw"]

	static fromRawObject(raw: any): DailyHistory {
		const dailyHistory = new DailyHistory()
		dailyHistory.id = raw.id
		dailyHistory.accountSource = raw.accountSource
		assignBigNumberProperties(dailyHistory, raw, DailyHistory.propertyList)
		return dailyHistory
	}

	public emptyOne(timestamp: number): DailyHistory {
		const dailyHistory = new DailyHistory()
		dailyHistory.id = `${timestamp}_`
		dailyHistory.accountSource = this.accountSource
		assignZeroBigNumberProperties(dailyHistory, DailyHistory.propertyList)
		return dailyHistory
	}

	public override applyDecimals(decimals: number): DailyHistory {
		return super.doApplyDecimals(decimals, DailyHistory.withDecimalsProperties) as DailyHistory
	}
}

export class SolverDailyHistory extends BaseHistory {
	tradeVolume?: BigNumber
	averagePositionSize?: BigNumber
	positionsCount?: BigNumber
	fundingPaid?: BigNumber
	fundingReceived?: BigNumber
	openInterest?: BigNumber
	timestamp?: BigNumber
	solver?: string

	static propertyList = ["tradeVolume", "averagePositionSize", "positionsCount", "fundingPaid", "fundingReceived", "openInterest", "timestamp"]
	static withDecimalsProperties = []

	static fromRawObject(raw: any): SolverDailyHistory {
		const history = new SolverDailyHistory()
		history.id = raw.id
		history.accountSource = raw.accountSource
		history.solver = raw.solver
		assignBigNumberProperties(history, raw, SolverDailyHistory.propertyList)
		return history
	}

	public emptyOne(timestamp: number): SolverDailyHistory {
		const history = new SolverDailyHistory()
		history.id = `${timestamp}_`
		history.accountSource = this.accountSource
		history.solver = this.solver
		assignZeroBigNumberProperties(history, SolverDailyHistory.propertyList)
		return history
	}

	public override applyDecimals(decimals: number): SolverDailyHistory {
		return super.doApplyDecimals(decimals, SolverDailyHistory.withDecimalsProperties) as SolverDailyHistory
	}
}

export class TotalHistory extends BaseHistory {
	quotesCount?: BigNumber
	tradeVolume?: BigNumber
	deposit?: BigNumber
	withdraw?: BigNumber
	allocate?: BigNumber
	deallocate?: BigNumber
	activeUsers?: BigNumber
	users?: BigNumber
	accounts?: BigNumber
	platformFee?: BigNumber
	openInterest?: BigNumber

	static propertyList = [
		"quotesCount",
		"tradeVolume",
		"deposit",
		"withdraw",
		"allocate",
		"deallocate",
		"activeUsers",
		"users",
		"accounts",
		"platformFee",
		"openInterest",
	]
	static withDecimalsProperties = ["deposit", "withdraw"]

	static fromRawObject(raw: any): TotalHistory {
		const history = new TotalHistory()
		history.id = raw.id
		history.accountSource = raw.accountSource
		assignBigNumberProperties(history, raw, TotalHistory.propertyList)
		return history
	}

	public emptyOne(timestamp: number): TotalHistory {
		return {} as any
	}

	public override applyDecimals(decimals: number): TotalHistory {
		return super.doApplyDecimals(decimals, TotalHistory.withDecimalsProperties) as TotalHistory
	}
}

export class WeeklyHistory extends BaseHistory {
	activeUsers?: BigNumber

	static propertyList = ["activeUsers"]
	static withDecimalsProperties = []

	static fromRawObject(raw: any): WeeklyHistory {
		const history = new WeeklyHistory()
		history.id = raw.id
		history.accountSource = raw.accountSource
		assignBigNumberProperties(history, raw, WeeklyHistory.propertyList)
		return history
	}

	public emptyOne(timestamp: number): WeeklyHistory {
		const history = new WeeklyHistory()
		history.id = `${timestamp}_`
		history.accountSource = this.accountSource
		assignZeroBigNumberProperties(history, WeeklyHistory.propertyList)
		return history
	}

	public override applyDecimals(decimals: number): WeeklyHistory {
		return super.doApplyDecimals(decimals, WeeklyHistory.withDecimalsProperties) as WeeklyHistory
	}
}

export class MonthlyHistory extends BaseHistory {
	activeUsers?: BigNumber

	static propertyList = ["activeUsers"]
	static withDecimalsProperties = []

	static fromRawObject(raw: any): MonthlyHistory {
		const history = new MonthlyHistory()
		history.id = raw.id
		history.accountSource = raw.accountSource
		assignBigNumberProperties(history, raw, MonthlyHistory.propertyList)
		return history
	}

	public emptyOne(timestamp: number): MonthlyHistory {
		const history = new MonthlyHistory()
		history.id = `${timestamp}_`
		history.accountSource = this.accountSource
		assignZeroBigNumberProperties(history, MonthlyHistory.propertyList)
		return history
	}

	public override applyDecimals(decimals: number): MonthlyHistory {
		return super.doApplyDecimals(decimals, MonthlyHistory.withDecimalsProperties) as MonthlyHistory
	}
}
