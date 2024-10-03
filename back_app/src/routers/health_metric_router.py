from typing import Dict

from fastapi import APIRouter
from sqlalchemy import select, and_

from src.app import db_session
from src.app.models import RuntimeConfiguration
from src.app.response_models import HealthMetric
from src.config import contexts

router = APIRouter(prefix="/health-metric", tags=["Health Metric"])


@router.get("/", response_model=Dict[str, HealthMetric | None])
async def get_health_metric():
    tenant_block = dict()
    with db_session() as session:
        for context in contexts:
            runtime_config: RuntimeConfiguration = session.scalars(
                select(RuntimeConfiguration).where(
                    and_(RuntimeConfiguration.tenant == context.tenant),
                )
            ).first()
            if runtime_config:
                latest_block = context.w3.eth.get_block("latest").number
                snapshot_block = runtime_config.lastSnapshotBlock or 0
                sync_block = runtime_config.lastSyncBlock or 0
                tenant_block[context.tenant] = HealthMetric(
                    latest_block=latest_block,
                    snapshot_block=snapshot_block,
                    sync_block=sync_block,
                    snapshot_block_lag=runtime_config.snapshotBlockLag,
                    diff_snapshot_block=latest_block - snapshot_block,
                    diff_sync_block=latest_block - sync_block,
                )
            else:
                tenant_block[context.tenant] = None
    return tenant_block
