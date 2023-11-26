import json
from dataclasses import dataclass
from typing import List

from context.context import ContextUtils


@dataclass
class Context:
    tenant: str
    subgraph_endpoint: str
    rpc: str
    symmio_address: str
    symmio_collateral_address: str
    symmio_multi_account: str
    symmio_liquidators: List[str]
    hedger_address: str
    hedger_max_open_interest_ratio: int

    # Binance
    binance_api_key: str
    binance_api_secret: str
    binance_email: str
    binance_is_master: bool

    deposit_diff: int
    from_unix_timestamp: int

    # Telegram
    telegram_group_id: str
    telegram_stat_group_id: int
    mention_for_red_alert_accounts: List[str]
    mention_for_red_alert_maintenance_accounts: List[str]
    mention_cooldown: int

    utils: ContextUtils | None


proxies = {}
server_port = 7231

# Intervals
fetch_stat_data_interval = 10
fetch_data_interval = 10
funding_fetch_data_interval = 10
update_binance_deposit_interval = 20

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
