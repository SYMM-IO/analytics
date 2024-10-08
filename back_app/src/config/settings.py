import json
from dataclasses import dataclass
from typing import List, Optional

import web3
from web3.middleware import geth_poa_middleware
from web3_collections import MultiEndpointHTTPProvider

from src.utils.attr_dict import AttrDict
from src.utils.binance_client import BinanceClient


@dataclass
class HedgerContextUtils:
    binance_client: Optional[BinanceClient]

    @staticmethod
    def from_context(context, fallback_binance_api_key, fallback_binance_api_secret):
        if CHAIN_ONLY:
            context = HedgerContextUtils(binance_client=None)
        else:
            context = HedgerContextUtils(
                binance_client=BinanceClient(context.binance_api_key, context.binance_api_secret)
                if len(context.binance_api_key) > 0
                else BinanceClient(fallback_binance_api_key, fallback_binance_api_secret),
            )
        return context


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

    def has_binance_keys(self) -> bool:
        return self.binance_api_key is not None and len(self.binance_api_key) > 0


@dataclass
class AffiliateContext:
    name: str  # Should be unique
    symmio_multi_account: str


@dataclass
class Context:
    tenant: str
    subgraph_endpoint: str
    rpcs: List[str]
    explorer: str
    explorer_api_keys: List[str]
    native_coin: str
    symmio_address: str
    symmio_collateral_address: str
    deploy_timestamp: int

    hedgers: List[HedgerContext]
    affiliates: List[AffiliateContext]
    liquidators: List[str]

    get_snapshot: bool

    # Telegram
    telegram_group_id: str
    telegram_stat_group_id: int
    mention_for_red_alert_accounts: List[str]
    mention_for_red_alert_maintenance_accounts: List[str]
    mention_cooldown: int

    w3: web3.Web3 = None
    historical_snapshot_step = 100

    def __post_init__(self):
        self.w3 = web3.Web3(
            MultiEndpointHTTPProvider(
                self.rpcs,
            )
        )
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
SNAPSHOT_INTERVAL = 2  # 120
SNAPSHOT_SCHEDULE = AttrDict(dict(affiliate=10, liquidator=30, hedger=5, hedger_binance=5))
SNAPSHOT_BLOCK_LAG = 10
SNAPSHOT_BLOCK_LAG_STEP = 25
DEBUG_MODE = False

with open("./src/config/abis/erc20abi.json", "r") as f:
    ERC20_ABI = json.load(f)

with open("./src/config/abis/abi.json", "r") as f:
    SYMMIO_ABI = json.load(f)

IGNORE_BINANCE_TRADE_VOLUME = True

# JWT setting
ACCESS_TOKEN_EXPIRE_TIME = 3 * 24 * 60 * 60  # 3 Days
JWT_ALGORITHM = "HS256"

CHAIN_ONLY = True

# # logging
# LOGGER = "analytics"
# FORMATTER = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(LOGGER)
# logger.setLevel(logging.DEBUG)
