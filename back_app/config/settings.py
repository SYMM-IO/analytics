import json
from dataclasses import dataclass
from typing import List

import web3
from web3.middleware import geth_poa_middleware

from config.context import HedgerContextUtils


@dataclass
class HedgerContext:
    name: str  # Should be unique
    binance_deposit_diff: int
    contract_deposit_diff: int
    wallets: List[str]

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


@dataclass
class Context:
    tenant: str
    subgraph_endpoint: str
    rpc: str
    explorer: str
    explorer_api_key: str
    native_coin: str
    symmio_address: str
    symmio_collateral_address: str
    deploy_timestamp: int

    hedgers: List[HedgerContext]
    affiliates: List[AffiliateContext]
    liquidators: List[str]

    # Telegram
    telegram_group_id: str
    telegram_stat_group_id: int
    mention_for_red_alert_accounts: List[str]
    mention_for_red_alert_maintenance_accounts: List[str]
    mention_cooldown: int

    w3: web3.Web3 = None
    historical_snapshot_step = 100

    def __post_init__(self):
        self.w3 = web3.Web3(web3.Web3.HTTPProvider(self.rpc))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    def hedger_with_name(self, hedger_name: str):
        for hedger in self.hedgers:
            if hedger.name == hedger_name:
                return hedger
        raise RuntimeError("Invalid Configuration")


PROXIES = {}
SERVER_PORT = 7231

# Intervals
FETCH_STAT_DATA_INTERVAL = 5 * 5
SNAPSHOT_INTERVAL = 2 * 5
SNAPSHOT_BLOCK_LAG = 30
DEBUG_MODE = True

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
