import BigNumber from "bignumber.js"

export class DailyHistory {
	[key: string]: string | BigNumber | undefined;

	id?: string
	quotesCount?: BigNumber
	tradeVolume?: BigNumber
	deposit?: BigNumber
	withdraw?: BigNumber
	allocate?: BigNumber
	deallocate?: BigNumber
	activeUsers?: BigNumber
	newUsers?: BigNumber
	newAccounts?: BigNumber
	platformFee?: BigNumber
	openInterest?: BigNumber
	accountSource?: string

	static fromRawObject(raw: any): DailyHistory {
		const dailyHistory = new DailyHistory()
		dailyHistory.id = raw.id
		dailyHistory.quotesCount = BigNumber(raw.quotesCount)
		dailyHistory.tradeVolume = BigNumber(raw.tradeVolume)
		dailyHistory.deposit = BigNumber(raw.deposit)
		dailyHistory.withdraw = BigNumber(raw.withdraw)
		dailyHistory.allocate = BigNumber(raw.allocate)
		dailyHistory.deallocate = BigNumber(raw.deallocate)
		dailyHistory.newUsers = BigNumber(raw.newUsers)
		dailyHistory.activeUsers = BigNumber(raw.activeUsers)
		dailyHistory.newAccounts = BigNumber(raw.newAccounts)
		dailyHistory.platformFee = BigNumber(raw.platformFee)
		dailyHistory.openInterest = BigNumber(raw.openInterest)
		dailyHistory.accountSource = raw.accountSource
		return dailyHistory
	}

	static emtpyOne(timestamp: string, accountSource = ""): DailyHistory {
		const dailyHistory = new DailyHistory()
		dailyHistory.id = timestamp + "_"
		dailyHistory.quotesCount = BigNumber(0)
		dailyHistory.tradeVolume = BigNumber(0)
		dailyHistory.deposit = BigNumber(0)
		dailyHistory.withdraw = BigNumber(0)
		dailyHistory.allocate = BigNumber(0)
		dailyHistory.deallocate = BigNumber(0)
		dailyHistory.newUsers = BigNumber(0)
		dailyHistory.activeUsers = BigNumber(0)
		dailyHistory.newAccounts = BigNumber(0)
		dailyHistory.platformFee = BigNumber(0)
		dailyHistory.openInterest = BigNumber(0)
		dailyHistory.accountSource = accountSource
		return dailyHistory
	}

	public static getTime(dh: DailyHistory): number | null {
		if (dh.id != null)
			return Number(dh.id?.split("_")[0])
		return null
	}
}

export class TotalHistory {
	[key: string]: string | BigNumber | undefined;

	id?: string
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
	accountSource?: string

	static fromRawObject(raw: any): TotalHistory {
		const dailyHistory = new TotalHistory()
		dailyHistory.id = raw.id
		dailyHistory.quotesCount = BigNumber(raw.quotesCount)
		dailyHistory.tradeVolume = BigNumber(raw.tradeVolume)
		dailyHistory.deposit = BigNumber(raw.deposit)
		dailyHistory.withdraw = BigNumber(raw.withdraw)
		dailyHistory.allocate = BigNumber(raw.allocate)
		dailyHistory.deallocate = BigNumber(raw.deallocate)
		dailyHistory.users = BigNumber(raw.users)
		dailyHistory.activeUsers = BigNumber(raw.activeUsers)
		dailyHistory.accounts = BigNumber(raw.accounts)
		dailyHistory.platformFee = BigNumber(raw.platformFee)
		dailyHistory.openInterest = BigNumber(raw.openInterest)
		dailyHistory.accountSource = raw.accountSource
		return dailyHistory
	}
}


export class AffiliateSnapshot {
	status_quotes?: string
	pnl_of_closed?: BigNumber
	pnl_of_liquidated?: BigNumber
	closed_notional_value?: BigNumber
	liquidated_notional_value?: BigNumber
	opened_notional_value?: BigNumber
	earned_cva?: BigNumber
	loss_cva?: BigNumber
	hedger_contract_allocated?: BigNumber
	hedger_upnl?: BigNumber
	all_contract_deposit?: BigNumber
	all_contract_withdraw?: BigNumber
	platform_fee?: BigNumber
	accounts_count?: number
	active_accounts?: number
	users_count?: number
	active_users?: number
	liquidator_states?: any
	trade_volume?: BigNumber
	timestamp?: string
	account_source?: string
	name?: string
	hedger_name?: string
	tenant?: string

	static fromRawObject(raw: any): AffiliateSnapshot {
		const snapshot = new AffiliateSnapshot()
		snapshot.status_quotes = raw.status_quotes
		snapshot.pnl_of_closed = BigNumber(raw.pnl_of_closed)
		snapshot.pnl_of_liquidated = BigNumber(raw.pnl_of_liquidated)
		snapshot.closed_notional_value = BigNumber(raw.closed_notional_value)
		snapshot.liquidated_notional_value = BigNumber(raw.liquidated_notional_value)
		snapshot.opened_notional_value = BigNumber(raw.opened_notional_value)
		snapshot.earned_cva = BigNumber(raw.earned_cva)
		snapshot.loss_cva = BigNumber(raw.loss_cva)
		snapshot.hedger_contract_allocated = BigNumber(raw.hedger_contract_allocated)
		snapshot.hedger_upnl = BigNumber(raw.hedger_upnl)
		snapshot.all_contract_deposit = BigNumber(raw.all_contract_deposit)
		snapshot.all_contract_withdraw = BigNumber(raw.all_contract_withdraw)
		snapshot.platform_fee = BigNumber(raw.platform_fee)
		snapshot.accounts_count = raw.accounts_count
		snapshot.active_accounts = raw.active_accounts
		snapshot.users_count = raw.users_count
		snapshot.active_users = raw.active_users
		snapshot.liquidator_states = raw.liquidator_states
		snapshot.trade_volume = BigNumber(raw.trade_volume)
		snapshot.timestamp = raw.timestamp
		snapshot.account_source = raw.account_source
		snapshot.name = raw.name
		snapshot.hedger_name = raw.hedger_name
		snapshot.tenant = raw.tenant
		return snapshot
	}
}


export class HedgerSnapshot {
	hedger_contract_balance?: BigNumber
	hedger_contract_deposit?: BigNumber
	hedger_contract_withdraw?: BigNumber
	max_open_interest?: BigNumber
	binance_maintenance_margin?: BigNumber
	binance_total_balance?: BigNumber
	binance_account_health_ratio?: BigNumber
	binance_cross_upnl?: BigNumber
	binance_av_balance?: BigNumber
	binance_total_initial_margin?: BigNumber
	binance_max_withdraw_amount?: BigNumber
	binance_deposit?: BigNumber
	binance_trade_volume?: BigNumber
	binance_paid_funding_fee?: BigNumber
	binance_received_funding_fee?: BigNumber
	users_paid_funding_fee?: BigNumber
	users_received_funding_fee?: BigNumber
	binance_next_funding_fee?: BigNumber
	binance_profit?: BigNumber
	contract_profit?: BigNumber
	earned_cva?: BigNumber
	loss_cva?: BigNumber
	liquidators_profit?: BigNumber
	liquidators_balance?: BigNumber
	liquidators_withdraw?: BigNumber
	liquidators_allocated?: BigNumber
	name?: string
	tenant?: string
	timestamp?: string

	totalState(): BigNumber {
		return (this?.binance_profit || BigNumber(0)).plus(this!.contract_profit!)
	}

	totalStateWithLiquidator(): BigNumber {
		return this.totalState().plus(this.liquidators_profit!)
	}

	fundingFeeProfit(): BigNumber {
		return (this.binance_received_funding_fee || BigNumber(0))
			.plus(this.binance_paid_funding_fee || BigNumber(0))
			.plus((this.users_received_funding_fee || BigNumber(0)).dividedBy(new BigNumber(10).pow(18)))
			.plus((this.users_paid_funding_fee || BigNumber(0)).dividedBy(new BigNumber(10).pow(18)))
	}

	returnOnInvestment(): BigNumber {
		return this.totalState()
			.div((this.binance_deposit || BigNumber(0)).plus(this.hedger_contract_deposit!))
			.multipliedBy(100)
	}

	returnOnInvestmentWithLiquidator(): BigNumber {
		return this.totalStateWithLiquidator()
			.div((this.binance_deposit || BigNumber(0)).plus(this.hedger_contract_deposit!))
			.multipliedBy(100)
	}

	static fromRawObject(raw: any): HedgerSnapshot {
		const snapshot = new HedgerSnapshot()
		snapshot.hedger_contract_balance = BigNumber(raw.hedger_contract_balance)
		snapshot.hedger_contract_deposit = BigNumber(raw.hedger_contract_deposit)
		snapshot.hedger_contract_withdraw = BigNumber(raw.hedger_contract_withdraw)
		snapshot.max_open_interest = BigNumberOf(raw.max_open_interest)
		snapshot.binance_maintenance_margin = BigNumberOf(raw.binance_maintenance_margin)
		snapshot.binance_total_balance = BigNumberOf(raw.binance_total_balance)
		snapshot.binance_account_health_ratio = BigNumberOf(raw.binance_account_health_ratio)
		snapshot.binance_cross_upnl = BigNumberOf(raw.binance_cross_upnl)
		snapshot.binance_av_balance = BigNumberOf(raw.binance_av_balance)
		snapshot.binance_total_initial_margin = BigNumberOf(raw.binance_total_initial_margin)
		snapshot.binance_max_withdraw_amount = BigNumberOf(raw.binance_max_withdraw_amount)
		snapshot.binance_deposit = BigNumberOf(raw.binance_deposit)
		snapshot.binance_trade_volume = BigNumberOf(raw.binance_trade_volume)
		snapshot.binance_paid_funding_fee = BigNumberOf(raw.binance_paid_funding_fee)
		snapshot.binance_received_funding_fee = BigNumberOf(raw.binance_received_funding_fee)
		snapshot.users_paid_funding_fee = BigNumberOf(raw.users_paid_funding_fee)
		snapshot.users_received_funding_fee = BigNumberOf(raw.users_received_funding_fee)
		snapshot.binance_next_funding_fee = BigNumberOf(raw.binance_next_funding_fee)
		snapshot.binance_profit = BigNumberOf(raw.binance_profit)
		snapshot.contract_profit = BigNumberOf(raw.contract_profit)
		snapshot.earned_cva = BigNumberOf(raw.earned_cva)
		snapshot.loss_cva = BigNumberOf(raw.loss_cva)
		snapshot.liquidators_profit = BigNumberOf(raw.liquidators_profit)
		snapshot.liquidators_balance = BigNumberOf(raw.liquidators_balance)
		snapshot.liquidators_withdraw = BigNumberOf(raw.liquidators_withdraw)
		snapshot.liquidators_allocated = BigNumberOf(raw.liquidators_allocated)
		snapshot.name = raw.name
		snapshot.tenant = raw.tenant
		snapshot.timestamp = raw.timestamp
		return snapshot
	}
}

export function BigNumberOf(value: any): undefined | BigNumber {
	return value == null ? undefined : BigNumber(value)
}