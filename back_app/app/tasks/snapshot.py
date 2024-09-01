import asyncio
import os
import traceback

from aioclock import AioClock, OnStartUp, OnShutDown, Every
from aioclock.group import Group

from config.local_settings import contexts

from app import db_session, log_transaction_context
from config.settings import SNAPSHOT_INTERVAL
from services.snapshot.snapshot_job import fetch_snapshot
from services.telegram_service import send_alert, escape_markdown_v1

# groups.py
group = Group()

# app.py
app = AioClock()
app.include_group(group)


def get_context():
    tenant = os.environ["TENANT"]
    for context in contexts:
        if context.tenant == tenant:
            return context
    raise Exception("Invalid context")


@group.task(trigger=Every(seconds=SNAPSHOT_INTERVAL))
async def run_snapshot():
    print("----------------- Running Snapshot ------------------")
    with db_session() as session:
        with log_transaction_context(session, fetch_snapshot.__name__) as log_tx:
            try:
                await fetch_snapshot(get_context(), session, log_tx)
            except Exception as e:
                traceback.print_exc()
                print(e)
                log_tx.add_data("traceback", traceback.format_exc())
                log_tx.add_data("error", str(e))

                send_alert(escape_markdown_v1(f"Snapshot task of {get_context().tenant} raised {e.__class__.__name__}\n {e}"))


@app.task(trigger=OnStartUp())
async def startup():
    print(f"Starting up snapshot task for {get_context().tenant}")


@app.task(trigger=OnShutDown())
async def shutdown():
    print(f"Shutting down snapshot task for {get_context().tenant}")


if __name__ == "__main__":
    asyncio.run(app.serve())
