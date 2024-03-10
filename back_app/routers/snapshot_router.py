from fastapi import APIRouter, Path, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import get_db_session
from app.models import AffiliateSnapshot, HedgerSnapshot

router = APIRouter(prefix="/snapshots", tags=["Snapshot"])


@router.get("/affiliate/{tenant}/{hedger}/{affiliate}")
async def get_affiliate_snapshot(
    tenant: str = Path(..., description="The tenant of this affiliate"),
    affiliate: str = Path(..., description="Name of the affiliate"),
    hedger: str = Path(..., description="Name of the hedger"),
    session: Session = Depends(get_db_session)
):
    query = (
        select(AffiliateSnapshot)
        .where(
            AffiliateSnapshot.tenant == tenant,
            AffiliateSnapshot.name == affiliate,
            AffiliateSnapshot.hedger_name == hedger,
        )
        .order_by(AffiliateSnapshot.timestamp.desc())
        .limit(1)
    )
    try:
        snapshot = session.scalar(query)
    except AffiliateSnapshot.DoesNotExist:
        snapshot = None

    return snapshot if snapshot else { }


@router.get("/hedger/{tenant}/{hedger}")
async def get_hedger_snapshot(
    tenant: str = Path(..., description="The tenant of this hedger"),
    hedger: str = Path(..., description="Name of the hedger"),
    session: Session = Depends(get_db_session)
):
    query = (
        select(HedgerSnapshot)
        .where(HedgerSnapshot.tenant == tenant, HedgerSnapshot.name == hedger)
        .order_by(HedgerSnapshot.timestamp.desc())
        .limit(1)
    )
    try:
        snapshot = session.scalar(query)
    except AffiliateSnapshot.DoesNotExist:
        snapshot = None

    return snapshot if snapshot else { }
