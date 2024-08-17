from app import db_session
from app.models import RuntimeConfiguration
from app.tasks.snapshot import get_context
from services.config_service import load_config
from services.snapshot.snapshot_job import do_fetch_snapshot
from utils.block import Block


def prepare_historical_snapshots():
    context = get_context()
    snapshot_block = Block.latest(context.w3)

    with db_session() as session:
        while snapshot_block.timestamp() > context.deploy_timestamp:
            config: RuntimeConfiguration = load_config(session, context)
            if config.lastHistoricalSnapshotBlock:
                snapshot_block = Block(context.w3, config.lastHistoricalSnapshotBlock)
            snapshot_block.backward(context.historical_snapshot_step)
            print(f"{context.tenant}: Historical snapshot for snapshot_block {snapshot_block.number} - {snapshot_block.datetime()}")
            if context.get_snapshot:
                do_fetch_snapshot(context, session, snapshot_block)
            config.lastHistoricalSnapshotBlock = snapshot_block.number
            session.commit()
