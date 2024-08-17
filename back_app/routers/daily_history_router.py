from datetime import datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import select, and_

from app import db_session
from app.models import DailyHistory, RuntimeConfiguration, DailyHistoryAffiliate
from config.local_settings import contexts

router = APIRouter(prefix="/history", tags=["Daily History"])


@router.get("/daily/{group_by}")
async def get_affiliate_history(group_by='day'):
    all_recs = dict()
    new_recs = dict()
    base_date = (datetime.today() - timedelta(days=3 * 365)).date()
    with db_session() as session:
        decimals = {context.tenant: context.decimals for context in session.scalars(select(RuntimeConfiguration)).all()}
        for context in contexts:
            for affiliate in context.affiliates:
                if affiliate.name not in all_recs:
                    all_recs[affiliate.name] = []
                all_recs[affiliate.name].extend(session.scalars(
                    select(DailyHistory).where(
                        and_(
                            DailyHistory.accountSource == affiliate.symmio_multi_account,
                            DailyHistory.tenant == context.tenant,
                            DailyHistory.timestamp >= base_date,
                        ))).all())
        for affiliate in all_recs:
            all_recs[affiliate].sort(key=lambda rec: rec.timestamp)
            try:
                rec = all_recs[affiliate][0]
                new_recs[affiliate] = [DailyHistoryAffiliate(quotesCount=rec.quotesCount, newUsers=rec.newUsers,
                                                             newAccounts=rec.newAccounts, activeUsers=rec.activeUsers,
                                                             tradeVolume=rec.tradeVolume,
                                                             deposit=rec.deposit * 10 ** (18 - decimals[rec.tenant]),
                                                             withdraw=rec.withdraw, allocate=rec.allocate,
                                                             deallocate=rec.deallocate, platformFee=rec.platformFee,
                                                             openInterest=rec.openInterest,
                                                             start_date=rec.timestamp.date())]
                for rec in all_recs[affiliate][1:]:
                    if rec.timestamp.date() == new_recs[affiliate][-1].start_date or (
                            group_by == 'week' and rec.timestamp.weekday()) or (
                            group_by == 'month' and rec.timestamp.day != 1):
                        new_recs[affiliate][-1].quotesCount += rec.quotesCount
                        new_recs[affiliate][-1].newUsers += rec.newUsers
                        new_recs[affiliate][-1].newAccounts += rec.newAccounts
                        new_recs[affiliate][-1].activeUsers += rec.activeUsers
                        new_recs[affiliate][-1].tradeVolume += rec.tradeVolume
                        new_recs[affiliate][-1].deposit += rec.deposit * 10 ** (18 - decimals[rec.tenant])
                        new_recs[affiliate][-1].withdraw += rec.withdraw
                        new_recs[affiliate][-1].allocate += rec.allocate
                        new_recs[affiliate][-1].deallocate += rec.deallocate
                        new_recs[affiliate][-1].platformFee += rec.platformFee
                        new_recs[affiliate][-1].openInterest += rec.openInterest
                    else:
                        new_recs[affiliate].append(
                            DailyHistoryAffiliate(quotesCount=rec.quotesCount, newUsers=rec.newUsers,
                                                  newAccounts=rec.newAccounts, activeUsers=rec.activeUsers,
                                                  tradeVolume=rec.tradeVolume,
                                                  deposit=rec.deposit * 10 ** (18 - decimals[rec.tenant]),
                                                  withdraw=rec.withdraw, allocate=rec.allocate,
                                                  deallocate=rec.deallocate, platformFee=rec.platformFee,
                                                  openInterest=rec.openInterest, start_date=rec.timestamp.date()))
            except IndexError:
                pass
        return new_recs


@router.get("/daily")
async def get_affiliate_daily_history():
    return await get_affiliate_history()


@router.get("/full/{until}")
async def _get_affiliate_full_history(until='today'):
    recs = await get_affiliate_history()
    result = {affiliate: DailyHistoryAffiliate(start_date=recs[affiliate][0].start_date) for affiliate in recs}
    for affiliate in recs:
        if until == 'yesterday' and recs[affiliate][-1].start_date == datetime.today().date():
            recs[affiliate].pop()
        for rec in recs[affiliate]:
            result[affiliate].quotesCount += rec.quotesCount
            result[affiliate].newUsers += rec.newUsers
            result[affiliate].tradeVolume += rec.tradeVolume
            result[affiliate].deposit += rec.deposit
            result[affiliate].withdraw += rec.withdraw
            result[affiliate].allocate += rec.allocate
            result[affiliate].deallocate += rec.deallocate
            result[affiliate].platformFee += rec.platformFee
            result[affiliate].openInterest += rec.openInterest
    return result


@router.get("/full")
async def get_affiliate_full_history():
    return await _get_affiliate_full_history()
