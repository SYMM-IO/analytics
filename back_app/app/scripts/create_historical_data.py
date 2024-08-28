import asyncio
from datetime import datetime, timedelta

from app import db_session
from app.models import RuntimeConfiguration
from app.tasks.snapshot import get_context
from services.config_service import load_config
from services.snapshot.snapshot_job import do_fetch_snapshot, sync_data
from utils.block import Block


async def prepare_historical_snapshots():
    context = get_context()
    snapshot_block = Block.latest(context.w3)
    last_snapshot_block = None
    with db_session() as session:
        await sync_data(context, session)
    begin_timestamp = (datetime.now() - timedelta(days=30)).timestamp()

    with db_session() as session:
        while snapshot_block.timestamp() > begin_timestamp:
            config: RuntimeConfiguration = load_config(session, context)
            if config.lastHistoricalSnapshotBlock:
                snapshot_block = Block(context.w3, config.lastHistoricalSnapshotBlock, last_snapshot_block)
            last_snapshot_block = snapshot_block.backward(context.historical_snapshot_step)
            print(f"{context.tenant}: Historical snapshot for snapshot_block {snapshot_block.number} - {snapshot_block.datetime()}")
            do_fetch_snapshot(context, session, snapshot_block, historical_mode=True)
            config.lastHistoricalSnapshotBlock = snapshot_block.number
            session.commit()


if __name__ == "__main__":
    asyncio.run(prepare_historical_snapshots())
