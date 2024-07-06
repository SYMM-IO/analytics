import json
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Numeric,
    Boolean,
    Text,
    Float,
    inspect,
)
from sqlalchemy.dialects.postgresql import JSON, insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

from utils.subgraph.subgraph_client_config import SubgraphClientConfig
from utils.time_utils import convert_timestamps

Base = declarative_base()


class BaseModel(Base):
    __is_timeseries__ = False
    __abstract__ = True

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self.__subgraph_client_config__ = None

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def upsert(self, session):
        conflict_less_dict = self.to_dict()
        if not conflict_less_dict[self.__pk_name__]:
            del conflict_less_dict[self.__pk_name__]

        insert_stmt = insert(self.__table__).values(**conflict_less_dict)
        update_dict = self.to_dict()
        do_update_stmt = insert_stmt.on_conflict_do_update(index_elements=[self.__pk_name__], set_=update_dict)
        session.execute(do_update_stmt)

    def save(self, session: Session):
        session.add(self)


class User(BaseModel):
    __tablename__ = "user"
    __is_timeseries__ = False
    __pk_name__ = "id"
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="users",
        pagination_field="timestamp",
        catch_up_field="timestamp",
        converter=convert_timestamps,
    )
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime)
    transaction = Column(String)
    tenant = Column(String, nullable=False)
    accounts = relationship("Account", back_populates="user")


class AdminUser(BaseModel):
    __tablename__ = "admin_user"
    __is_timeseries__ = False
    __pk_name__ = "username"
    username = Column(String, primary_key=True)
    password = Column(String)
    createTimestamp = Column(DateTime, default=datetime.now)


class Account(BaseModel):
    __tablename__ = "account"
    __is_timeseries__ = False
    __pk_name__ = "id"
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="accounts",
        pagination_field="timestamp",
        catch_up_field="updateTimestamp",
        name_maps={"user_id": "user"},
    )
    id = Column(String, primary_key=True)
    user = relationship("User", back_populates="accounts")
    user_id = Column(String, ForeignKey("user.id"))
    name = Column(String)
    accountSource = Column(String)
    quotesCount = Column(Integer)
    positionsCount = Column(Integer)
    transaction = Column(String)
    lastActivityTimestamp = Column(DateTime)
    timestamp = Column(DateTime)
    blockNumber = Column(Numeric(40, 0))
    updateTimestamp = Column(DateTime)
    tenant = Column(String, nullable=False)
    balanceChanges = relationship("BalanceChange", back_populates="account")
    quotes = relationship("Quote", back_populates="account")
    trade_histories = relationship("TradeHistory", back_populates="account")


class BalanceChange(BaseModel):
    __tablename__ = "balance_change"
    __is_timeseries__ = False
    __pk_name__ = "id"
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="balanceChanges",
        pagination_field="timestamp",
        catch_up_field="timestamp",
        name_maps={"account_id": "account"},
    )
    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("account.id"))
    account = relationship("Account", back_populates="balanceChanges")
    amount = Column(Numeric(40, 0), default=0)
    collateral = Column(String)
    type = Column(String)
    timestamp = Column(DateTime)
    blockNumber = Column(Numeric(40, 0))
    transaction = Column(String)
    tenant = Column(String, nullable=False)


class BalanceChangeType:
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    ALLOCATE_PARTY_A = "ALLOCATE_PARTY_A"
    DEALLOCATE_PARTY_A = "DEALLOCATE_PARTY_A"


class Symbol(BaseModel):
    __tablename__ = "symbol"
    __is_timeseries__ = False
    __pk_name__ = "id"
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="symbols",
        pagination_field="timestamp",
        catch_up_field="updateTimestamp",
        tenant_needed_fields=["id"],
        ignore_columns=["tenant", "main_market"],
    )
    id = Column(String, primary_key=True)
    name = Column(String)
    tradingFee = Column(Numeric(40, 0))
    timestamp = Column(DateTime)
    main_market = Column(Boolean, default=False)
    updateTimestamp = Column(DateTime)
    tenant = Column(String, nullable=False)
    quotes = relationship("Quote", back_populates="symbol")


class Quote(BaseModel):
    __tablename__ = "quote"
    __is_timeseries__ = False
    __pk_name__ = "id"
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="quotes",
        pagination_field="timestamp",
        catch_up_field="updateTimestamp",
        tenant_needed_fields=["id", "symbolId"],
        name_maps={"account_id": "account", "symbol_id": "symbolId"},
    )
    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("account.id"))
    account = relationship("Account", back_populates="quotes")
    symbol_id = Column(String, ForeignKey("symbol.id"))
    symbol = relationship("Symbol", back_populates="quotes")
    partyBsWhiteList = Column(Text)
    partyB = Column(String)
    positionType = Column(String)
    orderType = Column(String)
    collateral = Column(String)
    price = Column(Numeric(40, 0))
    marketPrice = Column(Numeric(40, 0))
    deadline = Column(Numeric(40, 0))
    quantity = Column(Numeric(40, 0))
    closedAmount = Column(Numeric(40, 0))
    cva = Column(Numeric(40, 0))
    partyAmm = Column(Numeric(40, 0))
    partyBmm = Column(Numeric(40, 0))
    lf = Column(Numeric(40, 0))
    quoteStatus = Column(Integer)
    blockNumber = Column(Numeric(40, 0))
    avgClosedPrice = Column(Numeric(40, 0))
    openPrice = Column(Numeric(40, 0), nullable=True)
    fundingPaid = Column(Numeric(40, 0), nullable=True)
    fundingReceived = Column(Numeric(40, 0), nullable=True)
    liquidatedSide = Column(Integer, nullable=True)
    transaction = Column(String)
    timestamp = Column(DateTime)
    updateTimestamp = Column(DateTime)
    tenant = Column(String, nullable=False)
    trade_histories = relationship("TradeHistory", back_populates="quote")


class TradeHistory(BaseModel):
    __tablename__ = "trade_history"
    __is_timeseries__ = False
    __pk_name__ = "id"
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="tradeHistories",
        pagination_field="timestamp",
        catch_up_field="updateTimestamp",
        tenant_needed_fields=["quote"],
        name_maps={"account_id": "account", "quote_id": "quote"},
    )
    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("account.id"))
    account = relationship("Account", back_populates="trade_histories")
    quote_id = Column(String, ForeignKey("quote.id"))
    quote = relationship("Quote", back_populates="trade_histories")
    volume = Column(Numeric(40, 0))
    blockNumber = Column(Integer)
    transaction = Column(String)
    quoteStatus = Column(Integer)
    timestamp = Column(DateTime)
    updateTimestamp = Column(DateTime)
    tenant = Column(String, nullable=False)


class DailyHistory(BaseModel):
    __tablename__ = "daily_history"
    __is_timeseries__ = True
    __pk_name__ = "timestamp"
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="dailyHistories",
        pagination_field="timestamp",
        catch_up_field="updateTimestamp",
    )
    id = Column(String)
    quotesCount = Column(Integer)
    newUsers = Column(Integer)
    accountSource = Column(String)
    newAccounts = Column(Integer)
    tradeVolume = Column(Numeric(40, 0))
    deposit = Column(Numeric(40, 0))
    withdraw = Column(Numeric(40, 0))
    allocate = Column(Numeric(40, 0))
    deallocate = Column(Numeric(40, 0))
    platformFee = Column(Numeric(40, 0))
    openInterest = Column(Numeric(40, 0))
    updateTimestamp = Column(DateTime)
    timestamp = Column(DateTime, primary_key=True)
    tenant = Column(String, nullable=False)


class RuntimeConfiguration(BaseModel):
    __tablename__ = "runtime_configuration"
    __is_timeseries__ = False
    __pk_name__ = "id"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    tenant = Column(String, nullable=False)
    decimals = Column(Integer)
    lastHistoricalSnapshotBlock = Column(Integer, nullable=True)
    lastSnapshotBlock = Column(Integer)
    deployTimestamp = Column(DateTime)

    def __repr__(self):
        return f"{self.name}, {self.tenant}"


class AffiliateSnapshot(BaseModel):
    __tablename__ = "affiliate_snapshot"
    __is_timeseries__ = True
    __pk_name__ = "timestamp"
    status_quotes = Column(Text)
    pnl_of_closed = Column(Numeric(40, 0))
    pnl_of_liquidated = Column(Numeric(40, 0))
    closed_notional_value = Column(Numeric(40, 0))
    liquidated_notional_value = Column(Numeric(40, 0))
    opened_notional_value = Column(Numeric(40, 0))
    earned_cva = Column(Numeric(40, 0))
    loss_cva = Column(Numeric(40, 0))
    hedger_contract_allocated = Column(Numeric(40, 0))
    hedger_upnl = Column(Numeric(40, 0))
    all_contract_deposit = Column(Numeric(40, 0))
    all_contract_withdraw = Column(Numeric(40, 0))
    platform_fee = Column(Numeric(40, 0), nullable=True)
    accounts_count = Column(Integer)
    active_accounts = Column(Integer)
    users_count = Column(Integer)
    active_users = Column(Integer)
    trade_volume = Column(Numeric(40, 0))
    timestamp = Column(DateTime, primary_key=True)
    block_number = Column(Numeric(40, 0))
    account_source = Column(String, nullable=False)
    name = Column(String, nullable=False, primary_key=True)
    hedger_name = Column(String, nullable=False, primary_key=True)
    tenant = Column(String, nullable=False, primary_key=True)

    def get_status_quotes(self):
        return json.loads(self.status_quotes.replace("'", '"'))


class LiquidatorSnapshot(BaseModel):
    __tablename__ = "liquidator_snapshot"
    __is_timeseries__ = True
    __pk_name__ = "timestamp"

    timestamp = Column(DateTime, primary_key=True)
    address = Column(String, nullable=False)
    withdraw = Column(Numeric(40, 0))
    balance = Column(Numeric(40, 0))
    allocated = Column(Numeric(40, 0))
    tenant = Column(String, nullable=False, primary_key=True)


class HedgerSnapshot(BaseModel):
    __tablename__ = "hedger_snapshot"
    __is_timeseries__ = True
    __pk_name__ = "timestamp"
    hedger_contract_balance = Column(Numeric(40, 0))
    hedger_contract_deposit = Column(Numeric(40, 0))
    hedger_contract_withdraw = Column(Numeric(40, 0))
    users_paid_funding_fee = Column(Numeric(40, 0), nullable=True)
    users_received_funding_fee = Column(Numeric(40, 0), nullable=True)
    contract_profit = Column(Numeric(40, 0), nullable=True)
    liquidators_profit = Column(Numeric(40, 0), nullable=True)
    total_deposit = Column(Numeric(40, 0), nullable=True)
    earned_cva = Column(Numeric(40, 0), nullable=True)
    loss_cva = Column(Numeric(40, 0), nullable=True)
    liquidators_balance = Column(Numeric(40, 0), nullable=True)
    liquidators_withdraw = Column(Numeric(40, 0), nullable=True)
    liquidators_allocated = Column(Numeric(40, 0), nullable=True)
    gas = Column(Numeric(40, 0), nullable=True)
    gas_dollar = Column(Numeric(40, 0), nullable=True)
    block_number = Column(Numeric(40, 0))
    name = Column(String, nullable=False, primary_key=True)
    tenant = Column(String, nullable=False, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)


class HedgerBinanceSnapshot(BaseModel):
    __tablename__ = "hedger_binance_snapshot"
    __is_timeseries__ = True
    __pk_name__ = "timestamp"
    max_open_interest = Column(Numeric(40, 0), nullable=True)
    binance_maintenance_margin = Column(Numeric(40, 0), nullable=True)
    binance_total_balance = Column(Numeric(40, 0), nullable=True)
    binance_account_health_ratio = Column(Numeric(40, 0), nullable=True)
    binance_cross_upnl = Column(Numeric(40, 0), nullable=True)
    binance_av_balance = Column(Numeric(40, 0), nullable=True)
    binance_total_initial_margin = Column(Numeric(40, 0), nullable=True)
    binance_max_withdraw_amount = Column(Numeric(40, 0), nullable=True)
    binance_deposit = Column(Numeric(40, 0), nullable=True)
    binance_trade_volume = Column(Numeric(40, 0), nullable=True)
    binance_paid_funding_fee = Column(Numeric(40, 0), nullable=True)
    binance_received_funding_fee = Column(Numeric(40, 0), nullable=True)
    users_paid_funding_fee = Column(Numeric(40, 0), nullable=True)
    users_received_funding_fee = Column(Numeric(40, 0), nullable=True)
    binance_next_funding_fee = Column(Numeric(40, 0), nullable=True)
    binance_profit = Column(Numeric(40, 0), nullable=True)
    total_deposit = Column(Numeric(40, 0), nullable=True)
    block_number = Column(Numeric(40, 0))
    name = Column(String, nullable=False, primary_key=True)
    tenant = Column(String, nullable=False, primary_key=True)
    timestamp = Column(DateTime, primary_key=True)


class BinanceIncome(BaseModel):
    __tablename__ = "binance_income"
    __is_timeseries__ = False
    __pk_name__ = "id"
    id = Column(Integer, primary_key=True)
    asset = Column(String)
    type = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime)
    tenant = Column(String, nullable=False)
    hedger = Column(String, nullable=False)


class BinanceTrade(BaseModel):
    __tablename__ = "binance_trade"
    __is_timeseries__ = False
    __pk_name__ = "id"
    id = Column(String, primary_key=True)
    symbol = Column(String)
    order_id = Column(String)
    side = Column(String)
    position_side = Column(String)
    qty = Column(Numeric(20, 6))
    price = Column(Numeric(20, 6))
    timestamp = Column(DateTime)
    tenant = Column(String, nullable=False)
    hedger = Column(String, nullable=False)


class StatsBotMessage(BaseModel):
    __tablename__ = "stats_bot_message"
    __is_timeseries__ = False
    __pk_name__ = "message_id"
    message_id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    content = Column(JSON)
    tenant = Column(String, nullable=False, primary_key=True)
