from fastapi import APIRouter
from sqlalchemy import select, and_

from app import db_session
from app.models import RuntimeConfiguration
from app.response_models import HealthMetric
from config.local_settings import contexts

router = APIRouter(prefix="/health-metric", tags=["Health Metric"])


@router.get("/", response_model=HealthMetric)
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
                tenant_block[context.tenant] = HealthMetric(context.w3.eth.get_block("latest").number,
                                                            runtime_config.lastSnapshotBlock,
                                                            runtime_config.lastSyncBlock,
                                                            runtime_config.snapshotBlockLag)
            else:
                tenant_block[context.tenant] = None
    return tenant_block
