import asyncio
import os

from aioclock import AioClock, OnStartUp, OnShutDown, Every
from aioclock.group import Group

from src.config import contexts
from src.config.settings import SNAPSHOT_INTERVAL
from src.services import load_all_messages, start_telegram_client, stop_telegram_client
from src.services.telegram_service import escape_markdown_v1, send_alert

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
    try:
        await start_telegram_client()
        await load_all_messages(get_context())
        await stop_telegram_client()
    except Exception as e:
        send_alert(escape_markdown_v1(f"StatsLoader task of {get_context().tenant} raised {e.__class__.__name__}\n {e}"))
        await stop_telegram_client()


@app.task(trigger=OnStartUp())
async def startup():
    print(f"Starting up StatsLoader task for {get_context().tenant}")


@app.task(trigger=OnShutDown())
async def shutdown():
    print(f"Shutting down StatsLoader task for {get_context().tenant}")


if __name__ == "__main__":
    asyncio.run(app.serve())
