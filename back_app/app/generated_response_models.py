from datetime import datetime
from pydantic import BaseModel


class AccountModel(BaseModel):
	id: str
	user_id: str
	name: str
	accountSource: str
	quotesCount: int
	positionsCount: int
	transaction: str
	lastActivityTimestamp: datetime
	timestamp: datetime
	blockNumber: int
	updateTimestamp: datetime
	tenant: str


class AdminUserModel(BaseModel):
	username: str
	password: str
	createTimestamp: datetime


class AffiliateSnapshotModel(BaseModel):
	status_quotes: str
	pnl_of_closed: int
	pnl_of_liquidated: int
	closed_notional_value: int
	liquidated_notional_value: int
	opened_notional_value: int
	earned_cva: int
	loss_cva: int
	hedger_contract_allocated: int
	hedger_upnl: int
	all_contract_deposit: int
	all_contract_withdraw: int
	platform_fee: int
	accounts_count: int
	active_accounts: int
	users_count: int
	active_users: int
	trade_volume: int
	timestamp: datetime
	block_number: int
	account_source: str
	name: str
	hedger_name: str
	tenant: str


class BalanceChangeModel(BaseModel):
	id: str
	account_id: str
	amount: int
	collateral: str
	type: str
	timestamp: datetime
	blockNumber: int
	transaction: str
	tenant: str


class BinanceIncomeModel(BaseModel):
	id: int
	asset: str
	type: str
	amount: float
	timestamp: datetime
	tenant: str
	hedger: str


class BinanceTradeModel(BaseModel):
	id: str
	symbol: str
	order_id: str
	side: str
	position_side: str
	qty: int
	price: int
	timestamp: datetime
	tenant: str
	hedger: str


class DailyHistoryModel(BaseModel):
	id: str
	quotesCount: int
	newUsers: int
	accountSource: str
	newAccounts: int
	activeUsers: int
	tradeVolume: int
	deposit: int
	withdraw: int
	allocate: int
	deallocate: int
	platformFee: int
	openInterest: int
	updateTimestamp: datetime
	timestamp: datetime
	tenant: str


class GasHistoryModel(BaseModel):
	address: str
	gas_amount: int
	initial_block: int
	tx_count: int
	tenant: str


class HedgerBinanceSnapshotModel(BaseModel):
	max_open_interest: int
	binance_maintenance_margin: int
	binance_total_balance: int
	binance_account_health_ratio: int
	binance_cross_upnl: int
	binance_av_balance: int
	binance_total_initial_margin: int
	binance_max_withdraw_amount: int
	binance_deposit: int
	binance_trade_volume: int
	binance_paid_funding_fee: int
	binance_received_funding_fee: int
	users_paid_funding_fee: int
	users_received_funding_fee: int
	binance_next_funding_fee: int
	binance_profit: int
	total_deposit: int
	block_number: int
	name: str
	tenant: str
	timestamp: datetime


class HedgerSnapshotModel(BaseModel):
	hedger_contract_balance: int
	hedger_contract_deposit: int
	hedger_contract_withdraw: int
	users_paid_funding_fee: int
	users_received_funding_fee: int
	contract_profit: int
	total_deposit: int
	earned_cva: int
	loss_cva: int
	gas: int
	block_number: int
	name: str
	tenant: str
	timestamp: datetime


class LiquidatorSnapshotModel(BaseModel):
	address: str
	withdraw: int
	balance: int
	allocated: int
	tenant: str
	timestamp: datetime


class QuoteModel(BaseModel):
	id: str
	account_id: str
	averageClosedPrice: int
	blockNumber: int
	closeDeadline: int
	closePrice: int
	closedAmount: int
	closedPrice: int
	cva: int
	fillAmount: int
	initialOpenedPrice: int
	lf: int
	liquidateAmount: int
	liquidatedSide: int
	liquidatePrice: int
	marketPrice: int
	maxFundingRate: int
	openDeadline: int
	openedPrice: int
	orderTypeClose: str
	orderTypeOpen: str
	partyA: str
	partyAmm: int
	partyB: str
	partyBmm: int
	partyBsWhiteList: str
	positionType: str
	quantity: int
	quantityToClose: int
	quoteStatus: int
	requestedOpenPrice: int
	symbol_id: str
	tenant: str
	timeStamp: datetime
	tradingFee: int
	userPaidFunding: int
	userReceivedFunding: int


class RuntimeConfigurationModel(BaseModel):
	id: int
	name: str
	tenant: str
	decimals: int
	lastHistoricalSnapshotBlock: int
	lastSnapshotBlock: int
	lastSyncBlock: int
	snapshotBlockLag: int
	deployTimestamp: datetime


class StatsBotMessageModel(BaseModel):
	message_id: int
	timestamp: datetime
	content: str
	tenant: str


class SymbolModel(BaseModel):
	id: str
	name: str
	tradingFee: int
	timestamp: datetime
	updateTimestamp: datetime
	tenant: str


class TradeHistoryModel(BaseModel):
	id: str
	account_id: str
	quote_id: str
	volume: int
	blockNumber: int
	transaction: str
	quoteStatus: int
	timestamp: datetime
	updateTimestamp: datetime
	tenant: str


class UserModel(BaseModel):
	id: str
	timestamp: datetime
	transaction: str
	tenant: str


