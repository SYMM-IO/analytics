from config.settings import Context, HedgerContext, AffiliateContext
from config.context import HedgerContextUtils

x_contexts = Context(
    tenant="X",
    subgraph_endpoint="",
    rpc="",
    explorer="",
    explorer_api_key="",
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

x_contexts.hedgers[0].utils = HedgerContextUtils.from_context(x_contexts.hedgers[0])
