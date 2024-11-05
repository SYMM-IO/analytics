from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Numeric, Text
from sqlalchemy.orm import relationship

from src.app import BaseModel
from src.utils.subgraph.subgraph_client_config import SubgraphClientConfig
from src.utils.time_utils import convert_timestamps


class User(BaseModel):
    __tablename__ = "user"
    __is_timeseries__ = False
    __pk_names__ = ["id"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="users",
        pagination_field="timestamp",
        tenant_needed_fields=["id"],
        converter=convert_timestamps,
    )
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime)
    transaction = Column(String)
    tenant = Column(String, nullable=False)
    accounts = relationship("Account", back_populates="user")


class Account(BaseModel):
    __tablename__ = "account"
    __is_timeseries__ = False
    __pk_names__ = ["id"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="accounts",
        pagination_field="timestamp",
        tenant_needed_fields=["user"],
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


class BalanceChangeType:
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    ALLOCATE_PARTY_A = "ALLOCATE_PARTY_A"
    DEALLOCATE_PARTY_A = "DEALLOCATE_PARTY_A"


class BalanceChange(BaseModel):
    __tablename__ = "balance_change"
    __is_timeseries__ = False
    __pk_names__ = ["id"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="balanceChanges",
        pagination_field="timestamp",
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


class Symbol(BaseModel):
    __tablename__ = "symbol"
    __is_timeseries__ = False
    __pk_names__ = ["id"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="symbols",
        pagination_field="timestamp",
        tenant_needed_fields=["id"],
        ignore_columns=["tenant"],
    )
    id = Column(String, primary_key=True)
    name = Column(String)
    tradingFee = Column(Numeric(40, 0))
    timestamp = Column(DateTime)
    updateTimestamp = Column(DateTime)
    tenant = Column(String, nullable=False)
    quotes = relationship("Quote", back_populates="symbol")


class Quote(BaseModel):
    __tablename__ = "quote"
    __is_timeseries__ = False
    __pk_names__ = ["id"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="quotes",
        pagination_field="timestamp",
        tenant_needed_fields=["id", "symbolId"],
        name_maps={"account_id": "partyA", "symbol_id": "symbolId"},
    )
    id = Column(String, primary_key=True)
    account = relationship("Account", back_populates="quotes")
    account_id = Column(String, ForeignKey("account.id"))
    averageClosedPrice = Column(Numeric(40, 0))
    blockNumber = Column(Numeric(40, 0))
    closeDeadline = Column(Numeric(40, 0))
    closePrice = Column(Numeric(40, 0))
    closedAmount = Column(Numeric(40, 0))
    closedPrice = Column(Numeric(40, 0))
    cva = Column(Numeric(40, 0))
    fillAmount = Column(Numeric(40, 0))
    initialCva = Column(Numeric(40, 0))
    initialLf = Column(Numeric(40, 0))
    initialOpenedPrice = Column(Numeric(40, 0))
    initialPartyAmm = Column(Numeric(40, 0))
    initialPartyBmm = Column(Numeric(40, 0))
    lf = Column(Numeric(40, 0))
    liquidateAmount = Column(Numeric(40, 0))
    liquidatedSide = Column(Integer, nullable=True)
    liquidatePrice = Column(Numeric(40, 0))
    marketPrice = Column(Numeric(40, 0))
    maxFundingRate = Column(Numeric(40, 0))
    openDeadline = Column(Numeric(40, 0))
    openedPrice = Column(Numeric(40, 0), nullable=True)
    orderTypeClose = Column(String)
    orderTypeOpen = Column(String)
    partyAmm = Column(Numeric(40, 0))
    partyB = Column(String)
    partyBmm = Column(Numeric(40, 0))
    partyBsWhiteList = Column(Text)
    positionType = Column(String)
    quantity = Column(Numeric(40, 0))
    quantityToClose = Column(Numeric(40, 0))
    quoteStatus = Column(Integer)
    requestedOpenPrice = Column(Numeric(40, 0))
    symbol = relationship("Symbol", back_populates="quotes")
    symbol_id = Column(String, ForeignKey("symbol.id"))
    tenant = Column(String, nullable=False)
    timestamp = Column(DateTime)
    timestampAcceptCancelCloseRequest = Column(DateTime)
    timestampAcceptCancelRequest = Column(DateTime)
    timestampChargeFundingRate = Column(DateTime)
    timestampEmergencyClosePosition = Column(DateTime)
    timestampExpireQuote = Column(DateTime)
    timestampFillCloseRequest = Column(DateTime)
    timestampForceCancelCloseRequest = Column(DateTime)
    timestampForceCancelQuote = Column(DateTime)
    timestampForceClosePosition = Column(DateTime)
    timestampLastFundingPayment = Column(DateTime)
    timestampLiquidatePositionsPartyA = Column(DateTime)
    timestampLiquidatePositionsPartyB = Column(DateTime)
    timestampLockQuote = Column(DateTime)
    timestampOpenPosition = Column(DateTime)
    timestampRequestToCancelCloseRequest = Column(DateTime)
    timestampRequestToCancelQuote = Column(DateTime)
    timestampRequestToClosePosition = Column(DateTime)
    timestampRequestToLimitClosePosition = Column(DateTime)
    timestampSendQuote = Column(DateTime)
    timestampUnlockQuote = Column(DateTime)
    trade_histories = relationship("TradeHistory", back_populates="quote")
    tradingFee = Column(Numeric(40, 0))
    userPaidFunding = Column(Numeric(40, 0))
    userReceivedFunding = Column(Numeric(40, 0))


class TradeHistory(BaseModel):
    __tablename__ = "trade_history"
    __is_timeseries__ = False
    __pk_names__ = ["id"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="tradeHistories",
        pagination_field="timestamp",
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
    __is_timeseries__ = False
    __pk_names__ = ["timestamp", "accountSource"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="dailyHistories",
        pagination_field="timestamp",
    )
    id = Column(String)
    quotesCount = Column(Integer)
    newUsers = Column(Integer)
    accountSource = Column(String, primary_key=True)
    newAccounts = Column(Integer)
    activeUsers = Column(Integer)
    tradeVolume = Column(Numeric(40, 0))
    openTradeVolume = Column(Numeric(40, 0))
    closeTradeVolume = Column(Numeric(40, 0))
    liquidateTradeVolume = Column(Numeric(40, 0))
    deposit = Column(Numeric(40, 0))
    withdraw = Column(Numeric(40, 0))
    allocate = Column(Numeric(40, 0))
    deallocate = Column(Numeric(40, 0))
    platformFee = Column(Numeric(40, 0))
    openInterest = Column(Numeric(40, 0))
    fundingPaid = Column(Numeric(40, 0))
    fundingReceived = Column(Numeric(40, 0))
    averagePositionSize = Column(Numeric(40, 0))
    positionsCount = Column(Numeric(40, 0))
    updateTimestamp = Column(DateTime)
    timestamp = Column(DateTime, primary_key=True)
    tenant = Column(String, nullable=False)


class WeeklyHistory(BaseModel):
    __tablename__ = "weekly_history"
    __is_timeseries__ = False
    __pk_names__ = ["timestamp", "accountSource"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="weeklyHistories",
        pagination_field="timestamp",
    )
    id = Column(String)
    activeUsers = Column(Integer)
    timestamp = Column(DateTime, primary_key=True)
    accountSource = Column(String, primary_key=True)
    tenant = Column(String, nullable=False)


class MonthlyHistory(BaseModel):
    __tablename__ = "monthly_history"
    __is_timeseries__ = False
    __pk_names__ = ["timestamp", "accountSource"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="monthlyHistories",
        pagination_field="timestamp",
    )
    id = Column(String)
    activeUsers = Column(Integer)
    timestamp = Column(DateTime, primary_key=True)
    accountSource = Column(String, primary_key=True)
    tenant = Column(String, nullable=False)


class SolverDailyHistory(BaseModel):
    __tablename__ = "solver_daily_history"
    __is_timeseries__ = False
    __pk_names__ = ["timestamp", "solver", "accountSource"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="solverDailyHistories",
        pagination_field="timestamp",
    )
    id = Column(String)
    accountSource = Column(String, primary_key=True)
    solver = Column(String, primary_key=True)
    tradeVolume = Column(Numeric(40, 0))
    openTradeVolume = Column(Numeric(40, 0))
    closeTradeVolume = Column(Numeric(40, 0))
    liquidateTradeVolume = Column(Numeric(40, 0))
    openInterest = Column(Numeric(40, 0))
    fundingPaid = Column(Numeric(40, 0))
    fundingReceived = Column(Numeric(40, 0))
    averagePositionSize = Column(Numeric(40, 0))
    positionsCount = Column(Numeric(40, 0))
    updateTimestamp = Column(DateTime)
    timestamp = Column(DateTime, primary_key=True)
    tenant = Column(String, nullable=False)


class TotalHistory(BaseModel):
    __tablename__ = "total_history"
    __is_timeseries__ = False
    __pk_names__ = ["accountSource", "collateral"]
    __subgraph_client_config__ = SubgraphClientConfig(
        method_name="totalHistories",
        pagination_field="timestamp",
    )
    accountSource = Column(String, primary_key=True)
    collateral = Column(String, primary_key=True)
    tradeVolume = Column(Numeric(40, 0))
    openTradeVolume = Column(Numeric(40, 0))
    closeTradeVolume = Column(Numeric(40, 0))
    liquidateTradeVolume = Column(Numeric(40, 0))
    deposit = Column(Numeric(40, 0))
    withdraw = Column(Numeric(40, 0))
    allocate = Column(Numeric(40, 0))
    deallocate = Column(Numeric(40, 0))
    platformFee = Column(Numeric(40, 0))
    fundingPaid = Column(Numeric(40, 0))
    fundingReceived = Column(Numeric(40, 0))
    accounts = Column(Integer)
    users = Column(Integer)
    quotesCount = Column(Integer)
    updateTimestamp = Column(DateTime)
    timestamp = Column(DateTime)
