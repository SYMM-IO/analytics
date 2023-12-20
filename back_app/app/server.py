import asyncio
from contextlib import asynccontextmanager

import uvicorn
from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client

from app.exception_handlers import ExceptionHandlers, ErrorCodeResponse
from config.local_settings import contexts
from config.settings import (
    fetch_data_interval,
    fetch_stat_data_interval,
    update_binance_deposit_interval,
    server_port,
)
from context.migrations import create_tables
from cronjobs import load_stats_messages_sync
from cronjobs import setup_telegram_client
from cronjobs.bot.analytics_bot import report_snapshots_to_telegram
from cronjobs.snapshot_job import fetch_snapshot
from endpoints.snapshot_router import router as snapshot_router
from utils.binance_utils import update_binance_deposit_v2
from utils.telegram_utils import send_alert, escape_markdown_v1

scheduler: AsyncIOScheduler
telegram_user_client: Client


async def create_scheduler():
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_listener(listener, EVENT_JOB_ERROR)
    for context in contexts:
        scheduler.add_job(
            func=load_stats_messages_sync,
            args=[context, telegram_user_client, asyncio.get_running_loop()],
            trigger="interval",
            seconds=fetch_stat_data_interval,
            id=context.tenant + "_load_stats_messages",
        )
        scheduler.add_job(
            func=fetch_snapshot,
            args=[context],
            trigger="interval",
            seconds=fetch_data_interval,
            id=context.tenant + "_fetch_snapshot",
        )
        scheduler.add_job(
            func=report_snapshots_to_telegram,
            args=[context],
            trigger="interval",
            seconds=fetch_data_interval,
            id=context.tenant + "_report_snapshot_to_telegram",
        )
        for hedger_context in context.hedgers:
            scheduler.add_job(
                func=update_binance_deposit_v2,
                args=[context, hedger_context],
                trigger="interval",
                seconds=update_binance_deposit_interval,
                id=context.tenant + "_update_binance_deposit_v2",
            )
        # scheduler.add_job(
        # 	func=lambda ctx=context: calculate_paid_funding(ctx),
        # 	trigger="interval",
        # 	seconds=funding_fetch_data_interval
        #   id=context.tenant + "_calculate_paid_funding"
        # )
        # scheduler.add_job(
        # 	func=lambda ctx=context: update_binance_deposit(ctx),
        # 	trigger="interval",
        # 	seconds=update_binance_deposit_interval
        #   id=context.tenant + "_update_binance_deposit"
        # )
    scheduler.start()


async def listener(event):
    global scheduler
    send_alert(
        escape_markdown_v1(
            f"BackgroundJob {event.job_id} raised {event.exception.__class__.__name__}\n {event.exception}"
        )
    )
    scheduler.shutdown(wait=False)
    await create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    create_tables()

    global telegram_user_client
    telegram_user_client = await setup_telegram_client()
    await telegram_user_client.start()

    await create_scheduler()
    yield
    scheduler.shutdown(wait=False)
    await telegram_user_client.stop()


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

app.include_router(snapshot_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run(app, port=server_port)
