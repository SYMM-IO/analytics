from datetime import datetime, date

from pydantic import BaseModel


class DailyHistoryAffiliate(BaseModel):
    quotesCount: int = 0
    newUsers: int = 0
    newAccounts: int = 0
    activeUsers: int = 0
    tradeVolume: int = 0
    deposit: int = 0
    withdraw: int = 0
    allocate: int = 0
    deallocate: int = 0
    platformFee: int = 0
    openInterest: int = 0
    start_date: date

    def __post_init__(self, quotesCount, newUsers, newAccounts, activeUsers, tradeVolume, deposit, withdraw, allocate,
                      deallocate, platformFee, openInterest, start_date):
        self.quotesCount = quotesCount
        self.newUsers = newUsers
        self.newAccounts = newAccounts
        self.activeUsers = activeUsers
        self.tradeVolume = tradeVolume
        self.deposit = deposit
        self.withdraw = withdraw
        self.allocate = allocate
        self.deallocate = deallocate
        self.platformFee = platformFee
        self.openInterest = openInterest
        self.start_date = start_date


class HealthMetric(BaseModel):
    latest_block: int
    snapshot_block: int
    sync_block: int
    snapshot_block_lag: int
    diff_snapshot_block: int
    diff_sync_block: int

    def __post_init__(self, latest_block, snapshot_block, sync_block, snapshot_block_lag, diff_snapshot_block,
                      diff_sync_block):
        self.latest_block = latest_block
        self.snapshot_block = snapshot_block
        self.sync_block = sync_block
        self.snapshot_block_lag = snapshot_block_lag
        self.diff_snapshot_block = diff_snapshot_block
        self.diff_sync_block = diff_sync_block


class ReadRoot(BaseModel):
    root_test: str


class Login(BaseModel):
    access_token: str


class ReadMe(BaseModel):
    username: str
    createTimestamp: datetime


class UserTradingVolume(BaseModel):
    user_id: str
    tenant: str
    address: str
    total_trading_volume: float
