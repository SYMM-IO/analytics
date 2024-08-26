from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import eq

from app import get_db_session
from app.generated_response_models import AffiliateSnapshotModel, HedgerSnapshotModel, LiquidatorSnapshotModel, \
    HedgerBinanceSnapshotModel
from app.models import AffiliateSnapshot, HedgerSnapshot, LiquidatorSnapshot, HedgerBinanceSnapshot

router = APIRouter(prefix="/snapshots", tags=["Snapshot"])


@router.get("/affiliate/{tenant}/{hedger}/{affiliate}", response_model=AffiliateSnapshotModel)
async def get_affiliate_snapshot(
        tenant: str = Path(..., description="The tenant of this affiliate"),
        affiliate: str = Path(..., description="Name of the affiliate"),
        hedger: str = Path(..., description="Name of the hedger"),
        session: Session = Depends(get_db_session),
):
    query = (
        select(AffiliateSnapshot).where(
            and_(
                eq(AffiliateSnapshot.tenant, tenant),
                eq(AffiliateSnapshot.name, affiliate),
                eq(AffiliateSnapshot.hedger_name, hedger),
            )
        ).order_by(
            AffiliateSnapshot.timestamp.desc()
        ).limit(1)
    )
    snapshot = session.scalar(query)
    if snapshot:
        return snapshot
    raise HTTPException(status_code=404, detail="Not found")


@router.get("/hedger/{tenant}/{hedger}", response_model=HedgerSnapshotModel)
async def get_hedger_snapshot(
        tenant: str = Path(..., description="The tenant of this hedger"),
        hedger: str = Path(..., description="Name of the hedger"),
        session: Session = Depends(get_db_session),
):
    query = (
        select(HedgerSnapshot).where(
            and_(
                eq(HedgerSnapshot.tenant, tenant),
                eq(HedgerSnapshot.name, hedger)),
        ).order_by(HedgerSnapshot.timestamp.desc()
                   ).limit(1)
    )
    snapshot = session.scalar(query)
    if snapshot:
        return snapshot
    raise HTTPException(status_code=404, detail="Not found")


@router.get("/liquidator/{tenant}/{address}", response_model=LiquidatorSnapshotModel)
async def get_liquidator_snapshot(
        tenant: str = Path(..., description="The tenant of this liquidator"),
        address: str = Path(..., description="Address of the liquidator"),
        session: Session = Depends(get_db_session),
):
    query = (
        select(LiquidatorSnapshot).where(
            and_(
                eq(LiquidatorSnapshot.tenant, tenant),
                eq(LiquidatorSnapshot.address, address),
            )
        ).order_by(
            LiquidatorSnapshot.timestamp.desc()
        ).limit(1)
    )
    snapshot = session.scalar(query)
    if snapshot:
        return snapshot
    raise HTTPException(status_code=404, detail="Not found")


@router.get("/hedger-binance/{tenant}/{hedger}", response_model=HedgerBinanceSnapshotModel)
async def get_hedger_binance_snapshot(
        tenant: str = Path(..., description="The tenant of this hedger"),
        hedger: str = Path(..., description="Name of the hedger"),
        session: Session = Depends(get_db_session),
):
    query = (
        select(HedgerBinanceSnapshot).where(
            and_(
                eq(HedgerBinanceSnapshot.tenant, tenant),
                eq(HedgerBinanceSnapshot.name, hedger),
            )
        ).order_by(
            HedgerBinanceSnapshot.timestamp.desc()
        ).limit(1)
    )
    snapshot = session.scalar(query)
    if snapshot:
        return snapshot
    raise HTTPException(status_code=404, detail="Not found")
