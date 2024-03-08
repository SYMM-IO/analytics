import os
import time

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler

from config.local_settings import contexts
from config.settings import FETCH_DATA_INTERVAL
from cronjobs.snapshot.snapshot_job import fetch_snapshot
from services.telegram_service import send_alert, escape_markdown_v1

scheduler: BackgroundScheduler


def listener(event):
    global scheduler
    send_alert(
        escape_markdown_v1(
            f"BackgroundJob {event.job_id} raised {event.exception.__class__.__name__}\n {event.exception}"
        )
    )
    scheduler.shutdown(wait=False)
    create_scheduler()


def create_scheduler():
    global scheduler
    context = get_context()
    scheduler = BackgroundScheduler()
    scheduler.add_listener(listener, EVENT_JOB_ERROR)
    scheduler.add_job(
        func=fetch_snapshot,
        args=[context],
        trigger="interval",
        seconds=FETCH_DATA_INTERVAL,
        id=context.tenant + "_fetch_snapshot",
    )
    scheduler.start()
    while True:
        time.sleep(10)


def get_context():
    tenant = os.environ["TENANT"]
    for context in contexts:
        if context.tenant == tenant:
            return context
    raise Exception("Invalid context")


if __name__ == "__main__":
    create_scheduler()
