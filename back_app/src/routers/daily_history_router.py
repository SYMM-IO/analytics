from datetime import datetime, timedelta
from typing import List, Dict

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, and_

from src.app import db_session
from src.app.models import DailyHistory, RuntimeConfiguration
from src.app.response_models import DailyHistoryAffiliate
from src.config import contexts

router = APIRouter(prefix="/history", tags=["Daily History"])


@router.get("/daily/{group_by}", response_model=Dict[str, List[DailyHistoryAffiliate]])
async def get_affiliate_history(group_by="day"):
    if group_by not in ["day", "week", "month"]:
        raise HTTPException(status_code=404, detail="Not found")
    daily_history = dict()
    daily_history_affiliate = dict()
    base_date = (datetime.today() - timedelta(days=3 * 365)).date()
    with db_session() as session:
        decimals = {context.tenant: context.decimals for context in session.scalars(select(RuntimeConfiguration)).all()}
        for context in contexts:
            for affiliate in context.affiliates:
                daily_history.setdefault(affiliate.name, []).extend(
                    session.scalars(
                        select(DailyHistory).where(
                            and_(
                                DailyHistory.accountSource == affiliate.symmio_multi_account,
                                DailyHistory.tenant == context.tenant,
                                DailyHistory.timestamp >= base_date,
                            )
                        )
                    ).all()
                )
        for affiliate in daily_history:
            daily_history[affiliate].sort(key=lambda rec: rec.timestamp)
            try:
                rec = daily_history[affiliate][0]
                daily_history_affiliate[affiliate] = [
                    DailyHistoryAffiliate(
                        quotesCount=rec.quotesCount,
                        newUsers=rec.newUsers,
                        newAccounts=rec.newAccounts,
                        activeUsers=rec.activeUsers,
                        tradeVolume=rec.tradeVolume,
                        deposit=rec.deposit * 10 ** (18 - decimals[rec.tenant]),
                        withdraw=rec.withdraw,
                        allocate=rec.allocate,
                        deallocate=rec.deallocate,
                        platformFee=rec.platformFee,
                        openInterest=rec.openInterest,
                        start_date=rec.timestamp.date(),
                    )
                ]
                for rec in daily_history[affiliate][1:]:
                    if (
                        rec.timestamp.date() == daily_history_affiliate[affiliate][-1].start_date
                        or (group_by == "week" and rec.timestamp.weekday())
                        or (group_by == "month" and rec.timestamp.day != 1)
                    ):
                        daily_history_affiliate[affiliate][-1].quotesCount += rec.quotesCount
                        daily_history_affiliate[affiliate][-1].newUsers += rec.newUsers
                        daily_history_affiliate[affiliate][-1].newAccounts += rec.newAccounts
                        daily_history_affiliate[affiliate][-1].activeUsers += rec.activeUsers
                        daily_history_affiliate[affiliate][-1].tradeVolume += rec.tradeVolume
                        daily_history_affiliate[affiliate][-1].deposit += rec.deposit * 10 ** (18 - decimals[rec.tenant])
                        daily_history_affiliate[affiliate][-1].withdraw += rec.withdraw
                        daily_history_affiliate[affiliate][-1].allocate += rec.allocate
                        daily_history_affiliate[affiliate][-1].deallocate += rec.deallocate
                        daily_history_affiliate[affiliate][-1].platformFee += rec.platformFee
                        daily_history_affiliate[affiliate][-1].openInterest += rec.openInterest
                    else:
                        daily_history_affiliate[affiliate].append(
                            DailyHistoryAffiliate(
                                quotesCount=rec.quotesCount,
                                newUsers=rec.newUsers,
                                newAccounts=rec.newAccounts,
                                activeUsers=rec.activeUsers,
                                tradeVolume=rec.tradeVolume,
                                deposit=rec.deposit * 10 ** (18 - decimals[rec.tenant]),
                                withdraw=rec.withdraw,
                                allocate=rec.allocate,
                                deallocate=rec.deallocate,
                                platformFee=rec.platformFee,
                                openInterest=rec.openInterest,
                                start_date=rec.timestamp.date(),
                            )
                        )
            except IndexError:
                pass
        return daily_history_affiliate


@router.get("/daily", response_model=Dict[str, List[DailyHistoryAffiliate]])
async def get_affiliate_daily_history():
    return await get_affiliate_history()


@router.get("/full/{until}", response_model=Dict[str, DailyHistoryAffiliate])
async def _get_affiliate_full_history(until="today"):
    if until not in ["today", "yesterday"]:
        raise HTTPException(status_code=404, detail="Not found")
    daily_history_affiliate = await get_affiliate_history()
    affiliate_full_history = {
        affiliate: DailyHistoryAffiliate(start_date=daily_history_affiliate[affiliate][0].start_date) for affiliate in daily_history_affiliate
    }
    for affiliate in daily_history_affiliate:
        if until == "yesterday" and daily_history_affiliate[affiliate][-1].start_date == datetime.today().date():
            daily_history_affiliate[affiliate].pop()
        for rec in daily_history_affiliate[affiliate]:
            affiliate_full_history[affiliate].quotesCount += rec.quotesCount
            affiliate_full_history[affiliate].newUsers += rec.newUsers
            affiliate_full_history[affiliate].tradeVolume += rec.tradeVolume
            affiliate_full_history[affiliate].deposit += rec.deposit
            affiliate_full_history[affiliate].withdraw += rec.withdraw
            affiliate_full_history[affiliate].allocate += rec.allocate
            affiliate_full_history[affiliate].deallocate += rec.deallocate
            affiliate_full_history[affiliate].platformFee += rec.platformFee
            affiliate_full_history[affiliate].openInterest += rec.openInterest
    return affiliate_full_history


@router.get("/full", response_model=Dict[str, DailyHistoryAffiliate])
async def get_affiliate_full_history():
    return await _get_affiliate_full_history()
