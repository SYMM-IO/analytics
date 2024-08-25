export interface HedgerSnapshotModel {
  hedger_contract_balance: number;
  hedger_contract_deposit: number;
  hedger_contract_withdraw: number;
  users_paid_funding_fee: number;
  users_received_funding_fee: number;
  contract_profit: number;
  total_deposit: number;
  earned_cva: number;
  loss_cva: number;
  gas: number;
  block_number: number;
  name: string;
  tenant: string;
  timestamp: number;
}

export interface UserTradingVolume {
  user_id: string;
  tenant: string;
  address: string;
  total_trading_volume: number;
}

export interface AffiliateSnapshotModel {
  status_quotes: string;
  pnl_of_closed: number;
  pnl_of_liquidated: number;
  closed_notional_value: number;
  liquidated_notional_value: number;
  opened_notional_value: number;
  earned_cva: number;
  loss_cva: number;
  hedger_contract_allocated: number;
  hedger_upnl: number;
  all_contract_deposit: number;
  all_contract_withdraw: number;
  platform_fee: number;
  accounts_count: number;
  active_accounts: number;
  users_count: number;
  active_users: number;
  trade_volume: number;
  timestamp: number;
  block_number: number;
  account_source: string;
  name: string;
  hedger_name: string;
  tenant: string;
}

export interface DailyHistoryAffiliate {
  quotesCount: number;
  newUsers: number;
  newAccounts: number;
  activeUsers: number;
  tradeVolume: number;
  deposit: number;
  withdraw: number;
  allocate: number;
  deallocate: number;
  platformFee: number;
  openInterest: number;
  start_date: number;
}

export interface Login {
  access_token: string;
}

export interface ReadRoot {
  root_test: string;
}

export interface LiquidatorSnapshotModel {
  address: string;
  withdraw: number;
  balance: number;
  allocated: number;
  tenant: string;
  timestamp: number;
}

export interface HealthMetric {
  latest_block: number;
  snapshot_block: number;
  sync_block: number;
  snapshot_block_lag: number;
  diff_snapshot_block: number;
  diff_sync_block: number;
}

export interface ReadMe {
  username: string;
  createTimestamp: number;
}

export interface HedgerBinanceSnapshotModel {
  max_open_interest: number;
  binance_maintenance_margin: number;
  binance_total_balance: number;
  binance_account_health_ratio: number;
  binance_cross_upnl: number;
  binance_av_balance: number;
  binance_total_initial_margin: number;
  binance_max_withdraw_amount: number;
  binance_deposit: number;
  binance_trade_volume: number;
  binance_paid_funding_fee: number;
  binance_received_funding_fee: number;
  users_paid_funding_fee: number;
  users_received_funding_fee: number;
  binance_next_funding_fee: number;
  binance_profit: number;
  total_deposit: number;
  block_number: number;
  name: string;
  tenant: string;
  timestamp: number;
}