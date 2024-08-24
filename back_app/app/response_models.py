from datetime import datetime

from pydantic import BaseModel


class DailyHistoryAffiliate(BaseModel):
    quotesCount: int
    newUsers: int
    newAccounts: int
    activeUsers: int
    tradeVolume: int
    deposit: int
    withdraw: int
    allocate: int
    deallocate: int
    platformFee: int
    openInterest: int
    start_date: int

    def __post_init__(self, quotesCount=0, newUsers=0, newAccounts=0, activeUsers=0, tradeVolume=0, deposit=0,
                      withdraw=0, allocate=0, deallocate=0, platformFee=0, openInterest=0, start_date=None):
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

    def __post_init__(self, latest_block, snapshot_block, sync_block, snapshot_block_lag):
        self.latest_block = latest_block
        self.snapshot_block = snapshot_block or 0
        self.sync_block = sync_block or 0
        self.snapshot_block_lag = snapshot_block_lag
        self.diff_snapshot_block = latest_block - self.snapshot_block
        self.diff_sync_block = latest_block - self.sync_block


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
