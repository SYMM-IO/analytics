from typing import List

from config.settings import Context
from context.context import ContextUtils

x_configuration = Context(
    tenant="",
    subgraph_endpoint="",
    rpc="",
    hedger_address="",
    hedger_max_open_interest_ratio=0,
    symmio_address="",
    symmio_collateral_address="",
    symmio_liquidators=["", ""],
    symmio_multi_account="",
    binance_api_key="",
    binance_api_secret="",
    binance_email="",
    binance_is_master=False,
    telegram_group_id="",
    deposit_diff=0,
    from_unix_timestamp=0,
    mention_for_red_alert_accounts=[],
    mention_for_red_alert_maintenance_accounts=[],
    mention_cooldown=0,
    telegram_stat_group_id=0,
    utils=None,
)
x_configuration.utils = ContextUtils.from_configuration(x_configuration)

contexts: List[Context] = [x_configuration]

# Telegram
telegram_alert_group_id = ""
telegram_bot_token = ""
telegram_client_api_id = 0
telegram_client_api_hash = ""
telegram_phone_number = ""

admin_api_key = ""
