import asyncio
import datetime

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from config.local_settings import contexts
from config.settings import FETCH_STAT_DATA_INTERVAL
from cronjobs import load_all_messages, start_telegram_client, stop_telegram_client
from services.telegram_service import send_alert, escape_markdown_v1

scheduler: AsyncIOScheduler


async def listener(event):
    global scheduler
    send_alert(escape_markdown_v1(f"BackgroundJob {event.job_id} raised {event.exception.__class__.__name__}\n {event.exception}"))
    scheduler.shutdown(wait=False)
    await stop_telegram_client()
    create_scheduler()


def create_scheduler():
    global scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_listener(listener, EVENT_JOB_ERROR)
    scheduler.add_job(func=start_telegram_client, trigger=DateTrigger(datetime.datetime.now()))
    for context in contexts:
        scheduler.add_job(
            func=load_all_messages,
            args=[context],
            trigger="interval",
            seconds=FETCH_STAT_DATA_INTERVAL,
            id=context.tenant + "_stat_bots_loader",
        )
    scheduler.start()
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    create_scheduler()
