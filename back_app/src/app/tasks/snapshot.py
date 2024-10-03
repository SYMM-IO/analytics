import asyncio
import os
import traceback
from datetime import datetime

from aioclock import AioClock, OnStartUp, OnShutDown, Every
from aioclock.group import Group

from src.app import db_session, log_transaction_context, log_span_context
from src.config import contexts
from src.config.settings import SNAPSHOT_INTERVAL
from src.services.snapshot.snapshot_job import fetch_snapshot
from src.services.telegram_service import send_alert, escape_markdown_v1

# groups.py
from src.utils.log_formatter import print_gantt_transaction

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
        context = get_context()
        with log_transaction_context(session, fetch_snapshot.__name__, context.tenant) as log_tx:
            transaction_id = log_tx.id

            def update_endpoint(current_endpoint, next_endpoint, exception):
                with log_span_context(session, "Update Endpoint", transaction_id) as span:
                    span.add_data("current_endpoint", f"{current_endpoint}")
                    span.add_data("next_endpoint", f"{next_endpoint}")
                    span.add_data("exception", f"{exception}")
                return True

            if not context.w3.provider.before_endpoint_update:
                context.w3.provider.before_endpoint_update = update_endpoint
            try:
                await fetch_snapshot(context, session, log_tx)
                log_tx.end_time = datetime.now()
            except Exception as e:
                traceback.print_exc()
                log_tx.add_data("traceback", traceback.format_exc())
                log_tx.add_data("error", str(e))
                log_tx.end_time = datetime.now()
                print_gantt_transaction(log_tx, f"log_file_{context.tenant}.txt")

                send_alert(escape_markdown_v1(f"Snapshot task of {context.tenant} raised {e.__class__.__name__}\n {e}"))


@app.task(trigger=OnStartUp())
async def startup():
    print(f"Starting up snapshot task for {get_context().tenant}")


@app.task(trigger=OnShutDown())
async def shutdown():
    print(f"Shutting down snapshot task for {get_context().tenant}")


if __name__ == "__main__":
    asyncio.run(app.serve())
