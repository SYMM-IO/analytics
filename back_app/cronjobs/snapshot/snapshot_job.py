from datetime import datetime, timedelta, timezone

import web3
from web3.middleware import geth_poa_middleware

from app import db_session
from app.models import (
    RuntimeConfiguration,
    User,
    Symbol,
    Account,
    BalanceChange,
    Quote,
    TradeHistory,
    DailyHistory,
)
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
from utils.block import Block


def fetch_snapshot(context: Context):
    print("----------------------Prepare Snapshot----------------------------")
    with db_session() as session:
        config: RuntimeConfiguration = load_config(session, context)  # Configuration may have changed during this method
        config.nextSnapshotTimestamp = datetime.now(timezone.utc) - timedelta(minutes=5)  # for subgraph sync time
        config.upsert(session)

        for hedger_context in context.hedgers:
            if hedger_context.utils.binance_client:
                fetch_binance_income_histories(session, context, hedger_context)

        session.commit()

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

        session.commit()

        print(f"{context.tenant}: Data loaded...\nPreparing snapshot data...")

        w3 = web3.Web3(web3.Web3.HTTPProvider(context.rpc))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        latest_block = Block.latest(w3)

        for affiliate_context in context.affiliates:
            for hedger_context in context.hedgers:
                prepare_affiliate_snapshot(
                    config,
                    context,
                    session,
                    affiliate_context,
                    hedger_context,
                    latest_block,
                )
                session.commit()
        for hedger_context in context.hedgers:
            prepare_hedger_snapshot(config, context, session, hedger_context, latest_block)
