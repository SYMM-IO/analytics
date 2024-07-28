from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_

from app import db_session
from app.exception_handlers import ExceptionHandlers, ErrorCodeResponse
from app.models import DailyHistory, RuntimeConfiguration, DailyHistoryAffiliate
from config.local_settings import contexts
from config.settings import (
    SERVER_PORT,
)
from routers.auth_router import router as auth_router
from routers.snapshot_router import router as snapshot_router
from routers.user_history_router import router as user_history_router
from utils.security_utils import get_current_user


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Symmio analytics",
)
app.add_exception_handler(Exception, ExceptionHandlers.unhandled_exception)
app.add_exception_handler(HTTPException, ExceptionHandlers.http_exception)
app.add_exception_handler(ErrorCodeResponse, ExceptionHandlers.error_code_response)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(snapshot_router, dependencies=(Depends(get_current_user),))
app.include_router(user_history_router, dependencies=(Depends(get_current_user),))
app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/daily-history")
async def get_affiliate_daily_history():
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
                new_recs[affiliate] = [DailyHistoryAffiliate(quotesCount=rec.quotesCount,
                                                             newUsers=rec.newUsers,
                                                             newAccounts=rec.newAccounts,
                                                             tradeVolume=rec.tradeVolume,
                                                             deposit=rec.deposit * 10 ** (18 - decimals[rec.tenant]),
                                                             withdraw=rec.withdraw,
                                                             allocate=rec.allocate,
                                                             deallocate=rec.deallocate,
                                                             platformFee=rec.platformFee,
                                                             openInterest=rec.openInterest,
                                                             timestamp=rec.timestamp.date(),
                                                             )]
                for rec in all_recs[affiliate][1:]:
                    if rec.timestamp.date() == new_recs[affiliate][-1].timestamp:
                        new_recs[affiliate][-1].quotesCount += rec.quotesCount
                        new_recs[affiliate][-1].newUsers += rec.newUsers
                        new_recs[affiliate][-1].tradeVolume += rec.tradeVolume
                        new_recs[affiliate][-1].deposit += rec.deposit * 10 ** (18 - decimals[rec.tenant])
                        new_recs[affiliate][-1].withdraw += rec.withdraw
                        new_recs[affiliate][-1].allocate += rec.allocate
                        new_recs[affiliate][-1].deallocate += rec.deallocate
                        new_recs[affiliate][-1].platformFee += rec.platformFee
                        new_recs[affiliate][-1].openInterest += rec.openInterest
                    else:
                        new_recs[affiliate].append(
                            DailyHistoryAffiliate(quotesCount=rec.quotesCount,
                                                  newUsers=rec.newUsers,
                                                  newAccounts=rec.newAccounts,
                                                  tradeVolume=rec.tradeVolume,
                                                  deposit=rec.deposit * 10 ** (18 - decimals[rec.tenant]),
                                                  withdraw=rec.withdraw,
                                                  allocate=rec.allocate,
                                                  deallocate=rec.deallocate,
                                                  platformFee=rec.platformFee,
                                                  openInterest=rec.openInterest,
                                                  timestamp=rec.timestamp.date(),
                                                  ))
            except IndexError:
                pass
        return new_recs


@app.get("/full-history")
async def get_affiliate_full_history():
    recs = await get_affiliate_daily_history()
    result = {affiliate: DailyHistoryAffiliate() for affiliate in recs}
    for affiliate in recs:
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


if __name__ == "__main__":
    uvicorn.run(app, port=SERVER_PORT)
