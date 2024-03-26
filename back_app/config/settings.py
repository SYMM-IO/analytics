import json
from dataclasses import dataclass
from typing import List

from context.context import ContextUtils, HedgerContextUtils


@dataclass
class HedgerContext:
    name: str  # Should be unique
    binance_deposit_diff: int
    contract_deposit_diff: int

    hedger_address: str
    hedger_max_open_interest_ratio: int

    # Binance
    binance_api_key: str
    binance_api_secret: str
    binance_email: str
    binance_is_master: bool

    utils: HedgerContextUtils | None


@dataclass
class AffiliateContext:
    name: str  # Should be unique
    symmio_multi_account: str
    symmio_liquidators: List[str]


@dataclass
class Context:
    tenant: str
    subgraph_endpoint: str
    rpc: str
    symmio_address: str
    symmio_collateral_address: str
    from_unix_timestamp: int

    hedgers: List[HedgerContext]
    affiliates: List[AffiliateContext]

    # Telegram
    telegram_group_id: str
    telegram_stat_group_id: int
    mention_for_red_alert_accounts: List[str]
    mention_for_red_alert_maintenance_accounts: List[str]
    mention_cooldown: int

    utils: ContextUtils | None
    historical_snapshot_step = 100

    def hedger_with_name(self, hedger_name: str):
        for hedger in self.hedgers:
            if hedger.name == hedger_name:
                return hedger
        raise RuntimeError("Invalid Configuration")


PROXIES = {}
SERVER_PORT = 7231

# Intervals
FETCH_STAT_DATA_INTERVAL = 30 * 60
FETCH_DATA_INTERVAL = 2 * 60

# Alerting system
FUNDING_RATE_ALERT_THRESHOLD = 100
CLOSABLE_FUNDING_RATE_ALERT_THRESHOLD = 100

# DB
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = 5432

with open("./config/abis/erc20abi.json", "r") as f:
    ERC20_ABI = json.load(f)

with open("./config/abis/abi.json", "r") as f:
    SYMMIO_ABI = json.load(f)

IGNORE_BINANCE_TRADE_VOLUME = True

# JWT setting
ACCESS_TOKEN_EXPIRE_TIME = 3 * 24 * 60 * 60  # 3 Days
JWT_ALGORITHM = "HS256"
JWT_SECRET_KEY = ""
