import json
from dataclasses import dataclass
from typing import List

from context.context import ContextUtils, HedgerContextUtils


@dataclass
class HedgerContext:
    name: str  # Should be unique
    deposit_diff: int

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
    hedger_name: str  # The name of hedger in hedgerContext


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

    def hedger_for_affiliate(self, affiliate_name: str):
        for affiliate in self.affiliates:
            if affiliate.name == affiliate_name:
                for hedger in self.hedgers:
                    if hedger.name == affiliate.hedger_name:
                        return hedger
        raise RuntimeError("Invalid Configuration")

    def hedger_with_name(self, hedger_name: str):
        for hedger in self.hedgers:
            if hedger.name == hedger_name:
                return hedger
        raise RuntimeError("Invalid Configuration")


proxies = {}
server_port = 7231

# Intervals
fetch_stat_data_interval = 2 * 60
fetch_data_interval = 2 * 61
funding_fetch_data_interval = 30 * 60

# Alerting system
funding_rate_alert_threshold = 100
closable_funding_rate_alert_threshold = 100
main_market_symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "BCHUSDT",
    "XRPUSDT",
    "EOSUSDT",
    "LTCUSDT",
    "TRXUSDT",
    "ETCUSDT",
    "LINKUSDT",
    "XLMUSDT",
    "ADAUSDT",
    "XMRUSDT",
    "DASHUSDT",
    "ZECUSDT",
    "XTZUSDT",
    "BNBUSDT",
    "ATOMUSDT",
    "ONTUSDT",
    "IOTAUSDT",
    "BATUSDT",
]

# DB
db_name = "postgres"
db_user = "postgres"
db_password = "password"
db_host = "localhost"
db_port = 5432

with open("./config/abis/erc20abi.json", "r") as f:
    erc20_abi = json.load(f)

with open("./config/abis/abi.json", "r") as f:
    symmio_abi = json.load(f)
