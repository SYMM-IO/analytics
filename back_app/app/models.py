import json
from datetime import datetime
from decimal import Decimal
from typing import List
from dataclasses import dataclass

from peewee import *
from playhouse.postgres_ext import JSONField

from app import pg_db
from config.settings import Context
from services.snaphshot_service import get_last_affiliate_snapshot_for


class BaseModel(Model):
    class Meta:
        database = pg_db

    def upsert(self):
        fields = self._meta.fields
        data = {}
        for name, field in fields.items():
            data[field] = getattr(self, name)
        self.insert(**self.__data__).on_conflict(
            conflict_target=[
                fields["timestamp"] if self.is_timeseries() else fields["id"]
            ],
            update=data,
        ).execute()

    @staticmethod
    def is_timeseries():
        return False


class User(BaseModel):
    id = CharField(primary_key=True)
    timestamp = DateTimeField()
    transaction = CharField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class AdminUser(BaseModel):
    username = CharField(primary_key=True)
    password = CharField()
    createTimestamp = DateTimeField(default=datetime.now())

    @staticmethod
    def is_timeseries():
        return False


class Account(BaseModel):
    id = CharField(primary_key=True)
    user = ForeignKeyField(User, backref="accounts")
    name = CharField(null=True)
    accountSource = CharField(null=True)
    quotesCount = IntegerField()
    positionsCount = IntegerField()
    transaction = CharField()
    lastActivityTimestamp = DateTimeField()
    timestamp = DateTimeField()
    updateTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class BalanceChangeType:
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    ALLOCATE_PARTY_A = "ALLOCATE_PARTY_A"
    DEALLOCATE_PARTY_A = "DEALLOCATE_PARTY_A"
    tenant = CharField(null=False)


class BalanceChange(BaseModel):
    id = CharField(primary_key=True)
    account = ForeignKeyField(Account, backref="balances")
    amount = DecimalField(max_digits=40, decimal_places=0, default=0)
    collateral = CharField()
    type = CharField()
    timestamp = DateTimeField()
    transaction = CharField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class DepositPartyA(BaseModel):
    id = CharField(primary_key=True)
    account = ForeignKeyField(Account, backref="deposits")
    amount = DecimalField(max_digits=40, decimal_places=0)
    blockNumber = IntegerField()
    transaction = CharField()
    timestamp = DateTimeField()
    updateTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class WithdrawPartyA(BaseModel):
    id = CharField(primary_key=True)
    account = ForeignKeyField(Account, backref="withdraws")
    amount = DecimalField(max_digits=40, decimal_places=0)
    blockNumber = IntegerField()
    transaction = CharField()
    timestamp = DateTimeField()
    updateTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class AllocatedPartyA(BaseModel):
    id = CharField(primary_key=True)
    account = ForeignKeyField(Account, backref="allocations")
    amount = DecimalField(max_digits=40, decimal_places=0)
    blockNumber = IntegerField()
    transaction = CharField()
    timestamp = DateTimeField()
    updateTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class DeallocatePartyA(BaseModel):
    id = CharField(primary_key=True)
    account = ForeignKeyField(Account, backref="deallocations")
    amount = DecimalField(max_digits=40, decimal_places=0)
    blockNumber = IntegerField()
    transaction = CharField()
    timestamp = DateTimeField()
    updateTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class Symbol(BaseModel):
    id = CharField(primary_key=True)
    name = CharField()
    tradingFee = DecimalField(max_digits=40, decimal_places=0)
    timestamp = DateTimeField()
    main_market = BooleanField(default=False)
    updateTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class Quote(BaseModel):
    id = CharField(primary_key=True)
    account = ForeignKeyField(Account, backref="quotes")
    symbolId = ForeignKeyField(Symbol, backref="quotes")
    partyBsWhiteList = TextField()
    partyB = CharField(null=True)
    positionType = CharField()
    orderType = CharField()
    collateral = CharField()
    price = DecimalField(max_digits=40, decimal_places=0)
    marketPrice = DecimalField(max_digits=40, decimal_places=0)
    deadline = DecimalField(max_digits=40, decimal_places=0)
    quantity = DecimalField(max_digits=40, decimal_places=0)
    closedAmount = DecimalField(max_digits=40, decimal_places=0)
    cva = DecimalField(max_digits=40, decimal_places=0)
    partyAmm = DecimalField(max_digits=40, decimal_places=0)
    partyBmm = DecimalField(max_digits=40, decimal_places=0)
    lf = DecimalField(max_digits=40, decimal_places=0)
    quoteStatus = CharField()
    blockNumber = DecimalField(max_digits=40, decimal_places=0)
    avgClosedPrice = DecimalField(max_digits=40, decimal_places=0)
    openPrice = DecimalField(max_digits=40, decimal_places=0, null=True)
    fundingPaid = DecimalField(max_digits=40, decimal_places=0, null=True)
    liquidatedSide = CharField(null=True)
    transaction = CharField()
    timestamp = DateTimeField()
    updateTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class TradeHistory(BaseModel):
    id = CharField(primary_key=True)
    account = ForeignKeyField(Account, backref="trade_histories")
    quote = ForeignKeyField(Quote, backref="quote_trade_histories")
    volume = DecimalField(max_digits=40, decimal_places=0)
    blockNumber = IntegerField()
    transaction = CharField()
    quoteStatus = CharField()
    timestamp = DateTimeField()
    updateTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class DailyHistory(BaseModel):
    id = CharField()
    quotesCount = IntegerField()
    newUsers = IntegerField()
    accountSource = CharField(null=True)
    newAccounts = IntegerField()
    tradeVolume = DecimalField(max_digits=40, decimal_places=0)
    deposit = DecimalField(max_digits=40, decimal_places=0)
    withdraw = DecimalField(max_digits=40, decimal_places=0)
    allocate = DecimalField(max_digits=40, decimal_places=0)
    deallocate = DecimalField(max_digits=40, decimal_places=0)
    platformFee = DecimalField(max_digits=40, decimal_places=0)
    openInterest = DecimalField(max_digits=40, decimal_places=0)
    updateTimestamp = DateTimeField()
    timestamp = DateTimeField(primary_key=True)
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return True


class RuntimeConfiguration(BaseModel):
    name = CharField()
    decimals = IntegerField()
    migrationVersion = IntegerField(default=0)
    lastSnapshotTimestamp = DateTimeField(default=datetime.fromtimestamp(0))
    nextSnapshotTimestamp = DateTimeField(default=datetime.fromtimestamp(0))
    deployTimestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class PaidFundingRate(BaseModel):
    symbol = CharField()
    timestamp = DateTimeField()
    amount = DecimalField(max_digits=40, decimal_places=0)
    tenant = CharField(null=False)


class AffiliateSnapshot(BaseModel):
    status_quotes = TextField()
    pnl_of_closed = DecimalField(max_digits=40, decimal_places=0)
    pnl_of_liquidated = DecimalField(max_digits=40, decimal_places=0)
    closed_notional_value = DecimalField(max_digits=40, decimal_places=0)
    liquidated_notional_value = DecimalField(max_digits=40, decimal_places=0)
    opened_notional_value = DecimalField(max_digits=40, decimal_places=0)
    earned_cva = DecimalField(max_digits=40, decimal_places=0)
    loss_cva = DecimalField(max_digits=40, decimal_places=0)
    hedger_contract_allocated = DecimalField(max_digits=40, decimal_places=0)
    hedger_upnl = DecimalField(max_digits=40, decimal_places=0)
    all_contract_deposit = DecimalField(max_digits=40, decimal_places=0)
    all_contract_withdraw = DecimalField(max_digits=40, decimal_places=0)
    platform_fee = DecimalField(max_digits=40, decimal_places=0, null=True)
    accounts_count = IntegerField()
    active_accounts = IntegerField()
    users_count = IntegerField()
    active_users = IntegerField()
    liquidator_states = JSONField()
    trade_volume = DecimalField(max_digits=40, decimal_places=0)
    timestamp = DateTimeField(primary_key=True)
    account_source = CharField(null=False)
    name = CharField(null=False)
    hedger_name = CharField(null=False)
    tenant = CharField(null=False)

    def get_status_quotes(self):
        return json.loads(self.status_quotes.replace("'", '"'))


class HedgerSnapshot(BaseModel):
    hedger_contract_balance = DecimalField(max_digits=40, decimal_places=0)
    hedger_contract_deposit = DecimalField(max_digits=40, decimal_places=0)
    hedger_contract_withdraw = DecimalField(max_digits=40, decimal_places=0)
    max_open_interest = DecimalField(max_digits=40, decimal_places=0, null=True)
    binance_maintenance_margin = DecimalField(
        max_digits=40, decimal_places=0, null=True
    )
    binance_total_balance = DecimalField(max_digits=40, decimal_places=0, null=True)
    binance_account_health_ratio = DecimalField(
        max_digits=40, decimal_places=0, null=True
    )
    binance_cross_upnl = DecimalField(max_digits=40, decimal_places=0, null=True)
    binance_av_balance = DecimalField(max_digits=40, decimal_places=0, null=True)
    binance_total_initial_margin = DecimalField(
        max_digits=40, decimal_places=0, null=True
    )
    binance_max_withdraw_amount = DecimalField(
        max_digits=40, decimal_places=0, null=True
    )
    binance_deposit = DecimalField(max_digits=40, decimal_places=0, null=True)
    binance_trade_volume = DecimalField(max_digits=40, decimal_places=0, null=True)
    paid_funding_rate = DecimalField(max_digits=40, decimal_places=0, null=True)
    received_funding_rate = DecimalField(max_digits=40, decimal_places=0, null=True)
    next_funding_rate = DecimalField(max_digits=40, decimal_places=0, null=True)
    binance_profit = DecimalField(max_digits=40, decimal_places=0, null=True)
    contract_profit = DecimalField(max_digits=40, decimal_places=0, null=True)
    liquidators_profit = DecimalField(max_digits=40, decimal_places=0, null=True)
    total_deposit = DecimalField(max_digits=40, decimal_places=0, null=True)
    earned_cva = DecimalField(max_digits=40, decimal_places=0, null=True)
    loss_cva = DecimalField(max_digits=40, decimal_places=0, null=True)
    liquidators_balance = DecimalField(max_digits=40, decimal_places=0, null=True)
    liquidators_withdraw = DecimalField(max_digits=40, decimal_places=0, null=True)
    liquidators_allocated = DecimalField(max_digits=40, decimal_places=0, null=True)
    name = CharField(null=False)
    tenant = CharField(null=False)
    timestamp = DateTimeField(primary_key=True)

    @staticmethod
    def is_timeseries():
        return True


class BinanceDeposit(BaseModel):
    asset = CharField()
    amount = FloatField()
    status = IntegerField()
    timestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class BinanceWithdraw(BaseModel):
    asset = CharField()
    amount = FloatField()
    status = IntegerField()
    timestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class BinanceTransfer(BaseModel):
    asset = CharField()
    amount = FloatField()
    status = CharField()
    frm = CharField()
    to = CharField()
    timestamp = DateTimeField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class BinanceIncome(BaseModel):
    asset = CharField()
    type = CharField()
    amount = FloatField()
    timestamp = DateTimeField()
    tenant = CharField(null=False)
    hedger = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class BinanceTrade(BaseModel):
    symbol = CharField()
    id = CharField(primary_key=True)
    order_id = CharField()
    side = CharField()
    position_side = CharField()
    qty = DecimalField(max_digits=20, decimal_places=6)
    price = DecimalField(max_digits=20, decimal_places=6)
    timestamp = DateTimeField()
    tenant = CharField(null=False)
    hedger = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False


class SymbolPrice(BaseModel):
    symbol = CharField()
    price = DecimalField(max_digits=20, decimal_places=6)
    timestamp = DateTimeField()

    @staticmethod
    def is_timeseries():
        return False


class FundingRate(BaseModel):
    symbol = CharField()
    rate = DecimalField(max_digits=20, decimal_places=10)
    timestamp = DateTimeField()

    @staticmethod
    def is_timeseries():
        return False


class StatsBotMessage(BaseModel):
    message_id = IntegerField(unique=True)
    timestamp = DateTimeField()
    content = TextField()
    tenant = CharField(null=False)

    @staticmethod
    def is_timeseries():
        return False
