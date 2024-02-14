from datetime import datetime, timedelta, timezone

from config.settings import (
    Context,
)
from cronjobs.data_loaders import (
    load_accounts,
    load_daily_histories,
    load_quotes,
    load_symbols,
    load_trade_histories,
    load_users,
    load_balance_changes,
)
from cronjobs.snapshot.affiliate_snapshot import prepare_affiliate_snapshot
from cronjobs.snapshot.hedger_snapshot import prepare_hedger_snapshot
from services.binance_service import (
    fetch_binance_income_histories,
)
from services.config_service import load_config


def fetch_snapshot(context: Context):
    print("----------------------Prepare Snapshot----------------------------")
    config = load_config(context)  # Configuration may have changed during this method
    config.nextSnapshotTimestamp = datetime.now(timezone.utc) - timedelta(
        minutes=5
    )  # for subgraph sync time
    config.upsert()

    for hedger_context in context.hedgers:
        if hedger_context.utils.binance_client:
            fetch_binance_income_histories(context, hedger_context)

    load_users(config, context)
    load_symbols(config, context)
    load_accounts(config, context)
    load_balance_changes(config, context)
    load_quotes(config, context)
    load_trade_histories(config, context)
    load_daily_histories(config, context)

    config = load_config(context)  # Configuration may have changed during this method
    config.lastSnapshotTimestamp = config.nextSnapshotTimestamp
    config.upsert()

    print(f"{context.tenant}: Data loaded...\nPreparing snapshot data...")

    for affiliate_context in context.affiliates:
        for hedger_context in context.hedgers:
            prepare_affiliate_snapshot(
                config, context, affiliate_context, hedger_context
            )
    for hedger_context in context.hedgers:
        prepare_hedger_snapshot(config, context, hedger_context)
