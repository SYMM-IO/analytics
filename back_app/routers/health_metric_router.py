from fastapi import APIRouter
from sqlalchemy import select, and_

from app import db_session
from app.models import RuntimeConfiguration, HealthMetric
from config.local_settings import contexts

router = APIRouter(prefix="/health-metric", tags=["Health Metric"])


@router.get("/")
async def get_last():
    tenant_block = {}
    with db_session() as session:
        for context in contexts:
            rec = session.scalars(
                select(RuntimeConfiguration).where(and_(RuntimeConfiguration.tenant == context.tenant))).all()
            if rec:
                tenant_block[context.tenant] = HealthMetric(context.w3.eth.get_block("latest").number,
                                                            rec[0].lastSnapshotBlock, rec[0].lastSyncBlock)
    return tenant_block
