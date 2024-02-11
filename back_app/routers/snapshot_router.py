from fastapi import APIRouter, Path

from app.models import AffiliateSnapshot, HedgerSnapshot
from utils.context_utils import get_context

router = APIRouter(prefix="/snapshots", tags=["Snapshot"])


@router.get("/affiliate/{tenant}//{hedger}/{affiliate}")
async def get_affiliate_snapshot(
    tenant: str = Path(..., description="The tenant of this affiliate"),
    affiliate: str = Path(..., description="Name of the affiliate"),
    hedger: str = Path(..., description="Name of the hedger"),
):
    query = (
        AffiliateSnapshot.select()
        .where(
            AffiliateSnapshot.tenant == tenant,
            AffiliateSnapshot.name == affiliate,
            AffiliateSnapshot.hedger_name == hedger,
        )
        .order_by(AffiliateSnapshot.timestamp.desc())
        .limit(1)
        .dicts()
    )
    try:
        snapshot = query.get()
    except AffiliateSnapshot.DoesNotExist:
        snapshot = None

    return snapshot if snapshot else {}


@router.get("/hedger/{tenant}/{hedger}")
async def get_hedger_snapshot(
    tenant: str = Path(..., description="The tenant of this hedger"),
    hedger: str = Path(..., description="Name of the hedger"),
):
    query = (
        HedgerSnapshot.select()
        .where(HedgerSnapshot.tenant == tenant, HedgerSnapshot.name == hedger)
        .order_by(HedgerSnapshot.timestamp.desc())
        .limit(1)
    )
    try:
        snapshot: HedgerSnapshot = query.get()
        context = get_context(tenant)
        snapshot.fill_calculated_fields(context)
    except HedgerSnapshot.DoesNotExist:
        snapshot = None

    return snapshot.to_dict() if snapshot else {}
