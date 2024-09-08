import re

from multicallable import Multicallable
from sqlalchemy.orm import Session

from app import log_span_context, LogTransaction
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


async def fetch_snapshot(context: Context, session: Session, log_tx: LogTransaction):
    sync_block = await sync_data(context, session, log_tx.id)
    log_tx.add_data("sync_block", sync_block.number)
    log_tx.add_data("get_snapshot", context.get_snapshot)
    log_tx.add_data("sync_only", not context.get_snapshot)
    if context.get_snapshot:
        do_fetch_snapshot(context, session, snapshot_block=sync_block, transaction_id=log_tx.id)


async def sync_data(context, session, log_tx_id):
    successful = True
    with log_span_context(session, "Sync Data With Subgraph", log_tx_id) as log_span:
        config: RuntimeConfiguration = load_config(session, context)
        config_details = log_object_properties(config)
        # logger.debug(f"{sync_data.__name__} :: {config_details=}")
        log_span.add_data("runtime_config", config_details)
        sync_block = Block.latest(context.w3)
        log_span.add_data("latest_block", sync_block.number)
        sync_block.backward(config.snapshotBlockLag)
        log_span.add_data("sync_block", sync_block.number)
        try:
            SubgraphClient(context, User).sync(session, sync_block)
            SubgraphClient(context, Symbol).sync(session, sync_block)
            SubgraphClient(context, Account).sync(session, sync_block)
            SubgraphClient(context, BalanceChange).sync(session, sync_block)
            SubgraphClient(context, Quote).sync(session, sync_block)
            SubgraphClient(context, TradeHistory).sync(session, sync_block)
            SubgraphClient(context, DailyHistory).sync(session, sync_block)
        except Exception as e:
            log_span.add_data("error", str(e))
            if "only indexed up to block number" in str(e):
                last_synced_block = int(re.search(r"indexed up to block number (\d+)", str(e)).group(1))
            elif "only has data starting at block number" in str(e):
                last_synced_block = int(re.search(r"has data starting at block number (\d+)", str(e)).group(1))
            else:
                raise e
            config = load_config(session, context)
            context.w3.provider.sort_endpoints()
            lag = Block.latest(context.w3).number - last_synced_block
            log_span.add_data("last_synced_block", last_synced_block)
            log_span.add_data("lag", lag)
            print(f"Last Synced Block is {last_synced_block} => Increasing snapshotBlockLag to {lag}")
            config.snapshotBlockLag = lag
            config.upsert(session)
            session.commit()
            successful = False  # To end the current span
    log_span.add_data("successful", successful)
    if not successful:
        return await sync_data(context, session, log_tx_id)
    else:
        print(f"{context.tenant}: =====> SYNC COMPLETED <=====")
        config.lastSyncBlock = sync_block.number
        config.snapshotBlockLag = max(config.snapshotBlockLag - SNAPSHOT_BLOCK_LAG_STEP, SNAPSHOT_BLOCK_LAG)
        config.upsert(session)
        session.commit()
        return sync_block


def do_fetch_snapshot(context: Context, session: Session, snapshot_block: Block, transaction_id, historical_mode=False):
    with log_span_context(session, "Fetch Snapshot", transaction_id) as log_span:
        config: RuntimeConfiguration = load_config(session, context)
        config_details = log_object_properties(config)
        log_span.add_data("runtime_config", config_details)
        log_span.add_data("snapshot_block", snapshot_block.number)
        multicallable = Multicallable(context.w3.to_checksum_address(context.symmio_address), SYMMIO_ABI, context.w3)
        snapshot_context = SnapshotContext(context, session, config, multicallable)

        if not historical_mode and Block(context.w3,
                                         config.lastSnapshotBlock).timestamp() >= snapshot_block.timestamp():
            # TODO: go to next rpc and try again
            return

        with log_span_context(session, "Prepare Affiliates Snapshots", transaction_id):
            for affiliate_context in context.affiliates:
                for hedger_context in context.hedgers:
                    with log_span_context(session, "Prepare Affiliate Snapshot", transaction_id) as span:
                        span.add_data("affiliate", affiliate_context.name)
                        span.add_data("hedger", hedger_context.name)
                        prepare_affiliate_snapshot(snapshot_context, affiliate_context, hedger_context, snapshot_block,
                                                   transaction_id)

        with log_span_context(session, "Prepare Liquidators Snapshots", transaction_id):
            for liquidator in context.liquidators:
                with log_span_context(session, "Prepare Liquidator Snapshot", transaction_id) as span:
                    span.add_data("liquidator", liquidator)
                    prepare_liquidator_snapshot(snapshot_context, liquidator, snapshot_block, transaction_id)

        with log_span_context(session, "Prepare Hedgers Snapshots", transaction_id) as span:
            span.add_data("chain_only", CHAIN_ONLY)
            for hedger_context in context.hedgers:
                with log_span_context(session, "Prepare Hedger Snapshot", transaction_id) as sp:
                    sp.add_data("hedger", hedger_context.name)
                    prepare_hedger_snapshot(snapshot_context, hedger_context, snapshot_block, transaction_id)

                if not CHAIN_ONLY and hedger_context.has_binance_keys():
                    with log_span_context(session, "Fetch Income Histories", transaction_id) as sp:
                        sp.add_data("hedger", hedger_context.name)
                        fetch_binance_income_histories(snapshot_context, hedger_context, transaction_id)
                    with log_span_context(session, "Prepare Hedger Binance Snapshot", transaction_id) as sp:
                        sp.add_data("hedger", hedger_context.name)
                        prepare_hedger_binance_snapshot(snapshot_context, hedger_context, snapshot_block,
                                                        transaction_id)
        if not historical_mode:
            config.lastSnapshotBlock = snapshot_block.number
            config.upsert(session)
    session.commit()
