import re

from multicallable import Multicallable
from sqlalchemy.orm import Session

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
    SYMMIO_ABI,
    SNAPSHOT_BLOCK_LAG,
    SNAPSHOT_BLOCK_LAG_STEP,
)
from services.binance_service import fetch_binance_income_histories
from services.config_service import load_config
from services.snapshot.affiliate_snapshot import prepare_affiliate_snapshot
from services.snapshot.hedger_binance_snapshot import prepare_hedger_binance_snapshot
from services.snapshot.hedger_snapshot import prepare_hedger_snapshot
from services.snapshot.liquidator_snapshot import prepare_liquidator_snapshot
from services.snapshot.snapshot_context import SnapshotContext
from utils.block import Block
from utils.subgraph.subgraph_client import SubgraphClient


async def fetch_snapshot(context: Context):
    with db_session() as session:
        sync_block = await sync_data(context, session)
        do_fetch_snapshot(context, session, snapshot_block=sync_block, prepare_binance_snapshot=False)


async def sync_data(context, session):
    config: RuntimeConfiguration = load_config(session, context)
    sync_block = Block.latest(context.w3)
    sync_block.backward(config.snapshotBlockLag)
    try:
        SubgraphClient(context, User).sync(session, sync_block)
        SubgraphClient(context, Symbol).sync(session, sync_block)
        SubgraphClient(context, Account).sync(session, sync_block)
        SubgraphClient(context, BalanceChange).sync(session, sync_block)
        SubgraphClient(context, Quote).sync(session, sync_block)
        SubgraphClient(context, TradeHistory).sync(session, sync_block)
        SubgraphClient(context, DailyHistory).sync(session, sync_block)
    except Exception as e:
        if "only indexed up to block number" in str(e):
            last_synced_block = int(re.search(r"indexed up to block number (\d+)", str(e)).group(1))
            config = load_config(session, context)
            lag = Block.latest(context.w3).number - last_synced_block
            print(f"Last Synced Block is {last_synced_block} => Increasing snapshotBlockLag to {lag}")
            config.snapshotBlockLag = lag
            config.upsert(session)
            session.commit()
            return await sync_data(context, session)
        else:
            raise e
    print(f"{context.tenant}: =====> SYNC COMPLETED <=====")
    config.lastSyncBlock = sync_block.number
    config.snapshotBlockLag = max(config.snapshotBlockLag - SNAPSHOT_BLOCK_LAG_STEP, SNAPSHOT_BLOCK_LAG)
    config.upsert(session)
    session.commit()
    return sync_block


def do_fetch_snapshot(context: Context, session: Session, snapshot_block: Block, prepare_binance_snapshot: bool = False):
    config: RuntimeConfiguration = load_config(session, context)
    multicallable = Multicallable(context.w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, context.w3)
    snapshot_context = SnapshotContext(context, session, config, multicallable)

    for affiliate_context in context.affiliates:
        for hedger_context in context.hedgers:
            prepare_affiliate_snapshot(
                snapshot_context,
                affiliate_context,
                hedger_context,
                snapshot_block,
            )
            session.commit()

    for liquidator in context.liquidators:
        prepare_liquidator_snapshot(snapshot_context, liquidator, snapshot_block)

    for hedger_context in context.hedgers:
        prepare_hedger_snapshot(snapshot_context, hedger_context, snapshot_block)

        if prepare_binance_snapshot and hedger_context.utils.binance_client:
            fetch_binance_income_histories(snapshot_context, hedger_context)
            prepare_hedger_binance_snapshot(snapshot_context, hedger_context, snapshot_block)

    config.lastSnapshotBlock = snapshot_block.number
    config.upsert(session)
    session.commit()
