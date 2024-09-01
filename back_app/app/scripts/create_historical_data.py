import asyncio
from datetime import datetime, timedelta

from app import db_session, log_span_context
from app.models import RuntimeConfiguration, LogTransaction
from app.tasks.snapshot import get_context
from services.config_service import load_config
from services.snapshot.snapshot_job import do_fetch_snapshot, sync_data
from utils.block import Block


async def prepare_historical_snapshots():
    context = get_context()
    with db_session() as session:
        transaction = LogTransaction(start_time=datetime.now(), label=f"{context.tenant} {prepare_historical_snapshots.__name__}")
        transaction.save(session)
        session.commit()
        snapshot_block = Block.latest(context.w3)
        last_snapshot_block = None
        await sync_data(context, session, log_tx_id=transaction.id)
        begin_timestamp = (datetime.now() - timedelta(days=30)).timestamp()

        while snapshot_block.timestamp() > begin_timestamp:
            with log_span_context(session, prepare_historical_snapshots.__name__, transaction.id) as span:
                config: RuntimeConfiguration = load_config(session, context)
                if config.lastHistoricalSnapshotBlock:
                    snapshot_block = Block(context.w3, config.lastHistoricalSnapshotBlock, last_snapshot_block)
                last_snapshot_block = snapshot_block.backward(context.historical_snapshot_step)
                span.data = dict(snapshot_block=snapshot_block.number, block_timestamp=snapshot_block.timestamp())
                print(f"{context.tenant}: Historical snapshot for snapshot_block {snapshot_block.number} - {snapshot_block.datetime()}")
                do_fetch_snapshot(context, session, snapshot_block, historical_mode=True, transaction_id=transaction.id)
                config.lastHistoricalSnapshotBlock = snapshot_block.number
        transaction.end_time = datetime.now()
        transaction.save(session)


if __name__ == "__main__":
    asyncio.run(prepare_historical_snapshots())
