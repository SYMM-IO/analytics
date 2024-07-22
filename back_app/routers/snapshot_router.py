from fastapi import APIRouter, Path, Depends
from sqlalchemy import and_, eq
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import get_db_session
from app.models import AffiliateSnapshot, HedgerSnapshot, LiquidatorSnapshot, HedgerBinanceSnapshot

router = APIRouter(prefix="/snapshots", tags=["Snapshot"])


@router.get("/affiliate/{tenant}/{hedger}/{affiliate}")
async def get_affiliate_snapshot(
    tenant: str = Path(..., description="The tenant of this affiliate"),
    affiliate: str = Path(..., description="Name of the affiliate"),
    hedger: str = Path(..., description="Name of the hedger"),
    session: Session = Depends(get_db_session),
):
    query = (
        select(AffiliateSnapshot)
        .where(and_(eq(AffiliateSnapshot.tenant, tenant), eq(AffiliateSnapshot.name, affiliate), eq(AffiliateSnapshot.hedger_name, hedger)))
        .order_by(AffiliateSnapshot.timestamp.desc())
        .limit(1)
    )
    snapshot = session.scalar(query)
    return snapshot if snapshot else {}


@router.get("/hedger/{tenant}/{hedger}")
async def get_hedger_snapshot(
    tenant: str = Path(..., description="The tenant of this hedger"),
    hedger: str = Path(..., description="Name of the hedger"),
    session: Session = Depends(get_db_session),
):
    query = (
        select(HedgerSnapshot)
        .where(and_(eq(HedgerSnapshot.tenant, tenant), eq(HedgerSnapshot.name, hedger)))
        .order_by(HedgerSnapshot.timestamp.desc())
        .limit(1)
    )
    snapshot = session.scalar(query)
    return snapshot if snapshot else {}


@router.get("/liquidator/{tenant}/{address}")
async def get_liquidator_snapshot(
    tenant: str = Path(..., description="The tenant of this liquidator"),
    address: str = Path(..., description="Address of the liquidator"),
    session: Session = Depends(get_db_session),
):
    query = (
        select(LiquidatorSnapshot)
        .where(and_(eq(LiquidatorSnapshot.tenant, tenant), eq(LiquidatorSnapshot.address, address)))
        .order_by(LiquidatorSnapshot.timestamp.desc())
        .limit(1)
    )
    snapshot = session.scalar(query)
    return snapshot if snapshot else {}


@router.get("/hedger-binance/{tenant}/{hedger}")
async def get_hedger_binance_snapshot(
    tenant: str = Path(..., description="The tenant of this hedger"),
    hedger: str = Path(..., description="Name of the hedger"),
    session: Session = Depends(get_db_session),
):
    query = (
        select(HedgerBinanceSnapshot)
        .where(and_(eq(HedgerBinanceSnapshot.tenant, tenant), eq(HedgerBinanceSnapshot.name, hedger)))
        .order_by(HedgerBinanceSnapshot.timestamp.desc())
        .limit(1)
    )
    snapshot = session.scalar(query)
    return snapshot if snapshot else {}
