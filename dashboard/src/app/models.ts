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

    static emtpyOne(timestamp: string, accountSource = ""): TotalHistory {
        const dailyHistory = new TotalHistory()
        dailyHistory.id = timestamp + "_"
        dailyHistory.quotesCount = BigNumber(0)
        dailyHistory.tradeVolume = BigNumber(0)
        dailyHistory.deposit = BigNumber(0)
        dailyHistory.withdraw = BigNumber(0)
        dailyHistory.allocate = BigNumber(0)
        dailyHistory.deallocate = BigNumber(0)
        dailyHistory.users = BigNumber(0)
        dailyHistory.activeUsers = BigNumber(0)
        dailyHistory.accounts = BigNumber(0)
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
    paid_funding_rate?: BigNumber
    next_funding_rate?: any
    name?: string
    tenant?: string
    timestamp?: string
    calculated_total_state?: number

    static fromRawObject(raw: any): HedgerSnapshot {
        const snapshot = new HedgerSnapshot()
        snapshot.hedger_contract_balance = BigNumber(raw.hedger_contract_balance)
        snapshot.hedger_contract_deposit = BigNumber(raw.hedger_contract_deposit)
        snapshot.hedger_contract_withdraw = BigNumber(raw.hedger_contract_withdraw)
        snapshot.max_open_interest = BigNumber(raw.max_open_interest)
        snapshot.binance_maintenance_margin = BigNumber(raw.binance_maintenance_margin)
        snapshot.binance_total_balance = BigNumber(raw.binance_total_balance)
        snapshot.binance_account_health_ratio = BigNumber(raw.binance_account_health_ratio)
        snapshot.binance_cross_upnl = BigNumber(raw.binance_cross_upnl)
        snapshot.binance_av_balance = BigNumber(raw.binance_av_balance)
        snapshot.binance_total_initial_margin = BigNumber(raw.binance_total_initial_margin)
        snapshot.binance_max_withdraw_amount = BigNumber(raw.binance_max_withdraw_amount)
        snapshot.binance_deposit = BigNumber(raw.binance_deposit)
        snapshot.binance_trade_volume = BigNumber(raw.binance_trade_volume)
        snapshot.paid_funding_rate = BigNumber(raw.paid_funding_rate)
        snapshot.next_funding_rate = raw.next_funding_rate
        snapshot.name = raw.name
        snapshot.tenant = raw.tenant
        snapshot.timestamp = raw.timestamp
        snapshot.calculated_total_state = raw.calculated_total_state
        return snapshot
    }
}