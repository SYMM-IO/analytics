from typing import List

from src.config.settings import Context, HedgerContext, AffiliateContext, HedgerContextUtils

x_context = Context(
    tenant="X",
    subgraph_endpoint="",
    rpcs=[""],
    explorer="",
    explorer_api_keys=[""],
    native_coin="ETH",
    symmio_address="",
    symmio_collateral_address="",
    hedgers=[
        HedgerContext(
            name="X_Hedger",
            hedger_address="",
            hedger_max_open_interest_ratio=20,
            binance_api_key="",
            binance_api_secret="",
            binance_email="",
            binance_is_master=False,
            binance_deposit_diff=0,
            contract_deposit_diff=0,
            utils=None,
            wallets=[],
        )
    ],
    affiliates=[
        AffiliateContext(
            name="x_affiliate",
            symmio_multi_account="",
        )
    ],
    liquidators=[],
    telegram_group_id="",
    deploy_timestamp=1693958400000,
    mention_for_red_alert_accounts=[],
    mention_for_red_alert_maintenance_accounts=[],
    mention_cooldown=10 * 60,
    telegram_stat_group_id=-1001968869688,
)

x_context.hedgers[0].utils = HedgerContextUtils.from_context(x_context.hedgers[0])

# Will be only used for fetching prices
fallback_binance_api_key: str = ""
fallback_binance_api_secret: str = ""

contexts: List[Context] = [
    x_context,
]
for context in contexts:
    for hedger in context.hedgers:
        hedger.utils = HedgerContextUtils.from_context(hedger, fallback_binance_api_key, fallback_binance_api_secret)

# DB
DB_NAME = ""
DB_USER = ""
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = 5432

# JWT
JWT_SECRET_KEY = ""

# Telegram
telegram_alert_group_id = ""
telegram_bot_token = ""
telegram_client_api_id = 0
telegram_client_api_hash = ""
telegram_phone_number = ""

admin_api_key = ""
