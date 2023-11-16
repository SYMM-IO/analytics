from app.models import Quote, DailyHistory, TradeHistory, Account, User, Symbol, BalanceChange
from context.context import gc
from context.graphql_client import Where
from utils.common_utils import convert_timestamps


def load_quotes(config):
    out = gc.load_all(
        lambda data: Quote(**convert_timestamps(data)),
        Quote,
        method="quotes",
        fields=[
            "transaction",
            "partyB",
            "timestamp",
            "updateTimestamp",
            "symbolId",
            "quantity",
            "price",
            "quoteStatus",
            "positionType",
            "collateral",
            "partyBsWhiteList",
            "orderType",
            "openPrice",
            "mm",
            "maxInterestRate",
            "marketPrice",
            "lf",
            "id",
            "cva",
            "deadline",
            "closedAmount",
            "blockNumber",
            "avgClosedPrice",
            "account",
            "liquidatedSide",
        ],
        pagination_field_name="timestamp",
        additional_conditions=[Where("updateTimestamp", "gte", str(int(config.updateTimestamp.timestamp())))],
        load_from_database=True,
        save_to_database=True,
    )
    for o in out:
        pass


def load_trade_histories(config):
    out = gc.load_all(
        lambda data: TradeHistory(**convert_timestamps(data)),
        TradeHistory,
        method="tradeHistories",
        fields=[
            "volume",
            "updateTimestamp",
            "transaction",
            "timestamp",
            "quoteStatus",
            "id",
            "blockNumber",
            "account",
            "quote",
        ],
        pagination_field_name="timestamp",
        additional_conditions=[Where("updateTimestamp", "gte", str(int(config.updateTimestamp.timestamp())))],
        load_from_database=False,
        save_to_database=True,
    )
    for o in out:
        pass


def load_accounts(config):
    out = gc.load_all(
        lambda data: Account(**convert_timestamps(data)),
        Account,
        method="accounts",
        fields=[
            "user",
            "updateTimestamp",
            "transaction",
            "timestamp",
            "quotesCount",
            "positionsCount",
            "name",
            "lastActivityTimestamp",
            "id",
            "accountSource",
        ],
        pagination_field_name="timestamp",
        additional_conditions=[
            Where("updateTimestamp", "gte", str(int(config.updateTimestamp.timestamp())))
        ],
        load_from_database=False,
        save_to_database=True,
    )
    for o in out:
        pass


def load_balance_changes(config):
    out = gc.load_all(
        lambda data: BalanceChange(**convert_timestamps(data)),
        BalanceChange,
        method="balanceChanges",
        fields=[
            "type",
            "transaction",
            "timestamp",
            "id",
            "collateral",
            "amount",
            "account",
        ],
        pagination_field_name="timestamp",
        load_from_database=True,
        save_to_database=True,
    )
    for o in out:
        pass


def load_users(config):
    out = gc.load_all(
        lambda data: User(**convert_timestamps(data)),
        User,
        method="users",
        fields=[
            "transaction",
            "timestamp",
            "id",
        ],
        pagination_field_name="timestamp",
        load_from_database=True,
        save_to_database=True,
    )
    for o in out:
        pass


def load_symbols(config):
    out = gc.load_all(
        lambda data: Symbol(**convert_timestamps(data)),
        Symbol,
        method="symbols",
        fields=[
            "name",
            "timestamp",
            "tradingFee",
            "updateTimestamp",
            "id",
        ],
        pagination_field_name="timestamp",
        additional_conditions=[Where("updateTimestamp", "gte", str(int(config.updateTimestamp.timestamp())))],
        load_from_database=False,
        save_to_database=True,
    )
    for o in out:
        pass


def load_daily_histories(config):
    out = gc.load_all(
        lambda data: DailyHistory(**convert_timestamps(data)),
        DailyHistory,
        method="dailyHistories",
        fields=[
            "id",
            "quotesCount",
            "tradeVolume",
            "deposit",
            "withdraw",
            "allocate",
            "deallocate",
            "activeUsers",
            "newUsers",
            "newAccounts",
            "platformFee",
            "openInterest",
            "accountSource",
            "updateTimestamp",
            "timestamp",
        ],
        pagination_field_name="timestamp",
        additional_conditions=[
            Where("updateTimestamp", "gte", str(int(config.updateTimestamp.timestamp()))),
        ],
        load_from_database=False,
        save_to_database=True,
    )
    for o in out:
        pass
