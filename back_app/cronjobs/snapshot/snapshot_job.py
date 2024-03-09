from datetime import datetime, timedelta, timezone

from app import db_session
from app.models import RuntimeConfiguration, User, Symbol, Account, BalanceChange, Quote, TradeHistory, DailyHistory
from config.settings import (
    Context,
)
from cronjobs.snapshot.affiliate_snapshot import prepare_affiliate_snapshot
from cronjobs.snapshot.hedger_snapshot import prepare_hedger_snapshot
from cronjobs.subgraph_synchronizer import SubgraphSynchronizer
from services.binance_service import (
    fetch_binance_income_histories,
)
from services.config_service import load_config


def fetch_snapshot(context: Context):
    print("----------------------Prepare Snapshot----------------------------")
    with db_session() as session:
        config: RuntimeConfiguration = load_config(session, context)  # Configuration may have changed during this method
        config.nextSnapshotTimestamp = datetime.now(timezone.utc) - timedelta(
            minutes=5
        )  # for subgraph sync time
        config.upsert(session)

        for hedger_context in context.hedgers:
            if hedger_context.utils.binance_client:
                fetch_binance_income_histories(session, context, hedger_context)

        SubgraphSynchronizer(context, User).sync(session)
        SubgraphSynchronizer(context, Symbol).sync(session)
        SubgraphSynchronizer(context, Account).sync(session)
        SubgraphSynchronizer(context, BalanceChange).sync(session)
        SubgraphSynchronizer(context, Quote).sync(session)
        SubgraphSynchronizer(context, TradeHistory).sync(session)
        SubgraphSynchronizer(context, DailyHistory).sync(session)

        config = load_config(session, context)  # Configuration may have changed during this method
        config.lastSnapshotTimestamp = config.nextSnapshotTimestamp
        config.upsert(session)

        print(f"{context.tenant}: Data loaded...\nPreparing snapshot data...")
        for affiliate_context in context.affiliates:
            for hedger_context in context.hedgers:
                prepare_affiliate_snapshot(config, context, session, affiliate_context, hedger_context)
        for hedger_context in context.hedgers:
            prepare_hedger_snapshot(config, context, session, hedger_context)
