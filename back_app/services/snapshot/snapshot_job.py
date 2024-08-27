import logging
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
    CHAIN_ONLY,
    LOGGER,
)
from services.binance_service import fetch_binance_income_histories
from services.config_service import load_config
from services.snapshot.affiliate_snapshot import prepare_affiliate_snapshot
from services.snapshot.hedger_binance_snapshot import prepare_hedger_binance_snapshot
from services.snapshot.hedger_snapshot import prepare_hedger_snapshot
from services.snapshot.liquidator_snapshot import prepare_liquidator_snapshot
from services.snapshot.snapshot_context import SnapshotContext
from utils.block import Block
from utils.model_utils import log_object_properties
from utils.subgraph.subgraph_client import SubgraphClient

logger = logging.getLogger(LOGGER)


async def fetch_snapshot(context: Context):
    with db_session() as session:
        sync_block = await sync_data(context, session)
        logger.debug(f'func={fetch_snapshot.__name__} -->  {sync_block=}')
        if context.get_snapshot:
            do_fetch_snapshot(context, session, snapshot_block=sync_block)


async def sync_data(context, session):
    config: RuntimeConfiguration = load_config(session, context)
    config_details = ", ".join(log_object_properties(config))
    logger.debug(f'func={sync_data.__name__} -->  {config_details=}')
    sync_block = Block.latest(context.w3)
    logger.debug(f'func={sync_data.__name__} -->  {sync_block=}')
    logger.debug(f'func={sync_data.__name__} -->  {sync_block.backward(config.snapshotBlockLag) = }')
    try:
        SubgraphClient(context, User).sync(session, sync_block)
        SubgraphClient(context, Symbol).sync(session, sync_block)
        SubgraphClient(context, Account).sync(session, sync_block)
        SubgraphClient(context, BalanceChange).sync(session, sync_block)
        SubgraphClient(context, Quote).sync(session, sync_block)
        SubgraphClient(context, TradeHistory).sync(session, sync_block)
        SubgraphClient(context, DailyHistory).sync(session, sync_block)
    except Exception as e:
        logger.error(e)
        if "only indexed up to block number" in str(e):
            last_synced_block = int(re.search(r"indexed up to block number (\d+)", str(e)).group(1))
        elif "only has data starting at block number" in str(e):
            last_synced_block = int(re.search(r"has data starting at block number (\d+)", str(e)).group(1))
        else:
            raise e
        config = load_config(session, context)
        context.w3.provider.sort_endpoints()
        lag = Block.latest(context.w3).number - last_synced_block
        logger.debug(f'func={sync_data.__name__} -->  {last_synced_block=}')
        logger.debug(f'func={sync_data.__name__} -->  {lag=}')
        print(f"Last Synced Block is {last_synced_block} => Increasing snapshotBlockLag to {lag}")
        config.snapshotBlockLag = lag
        config.upsert(session)
        session.commit()
        return await sync_data(context, session)
    print(f"{context.tenant}: =====> SYNC COMPLETED <=====")
    config.lastSyncBlock = sync_block.number
    config.snapshotBlockLag = max(config.snapshotBlockLag - SNAPSHOT_BLOCK_LAG_STEP, SNAPSHOT_BLOCK_LAG)
    config.upsert(session)
    session.commit()
    return sync_block


def do_fetch_snapshot(context: Context, session: Session, snapshot_block: Block, historical_mode=False):
    config: RuntimeConfiguration = load_config(session, context)
    config_details = ", ".join(log_object_properties(config))
    logger.debug(f'func={do_fetch_snapshot.__name__} -->  {config_details=}')
    logger.debug(f'func={do_fetch_snapshot.__name__} -->  {snapshot_block=}')
    multicallable = Multicallable(context.w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, context.w3)
    snapshot_context = SnapshotContext(context, session, config, multicallable)

    if not historical_mode and Block(context.w3, config.lastSnapshotBlock).timestamp() >= snapshot_block.timestamp():
        return

    for affiliate_context in context.affiliates:
        for hedger_context in context.hedgers:
            prepare_affiliate_snapshot(
                snapshot_context,
                affiliate_context,
                hedger_context,
                snapshot_block,
            )
            # session.commit()

    for liquidator in context.liquidators:
        prepare_liquidator_snapshot(snapshot_context, liquidator, snapshot_block)

    for hedger_context in context.hedgers:
        prepare_hedger_snapshot(snapshot_context, hedger_context, snapshot_block)

        if not CHAIN_ONLY and hedger_context.has_binance_keys():
            fetch_binance_income_histories(snapshot_context, hedger_context)
            prepare_hedger_binance_snapshot(snapshot_context, hedger_context, snapshot_block)

    config.lastSnapshotBlock = snapshot_block.number
    config.upsert(session)
    session.commit()
