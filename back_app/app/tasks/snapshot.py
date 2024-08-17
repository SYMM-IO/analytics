import asyncio
import logging
import os
import traceback

from aioclock import AioClock, OnStartUp, OnShutDown, Every
from aioclock.group import Group

from config.local_settings import contexts, LOG_PATH
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


formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
log_file = logging.FileHandler(f'log_file_{get_context().tenant}.log', 'w')
log_file.setFormatter(formatter)
logger.addHandler(log_file)


@group.task(trigger=Every(seconds=SNAPSHOT_INTERVAL))
async def run_snapshot():
    print("----------------- Running Snapshot ------------------")
    try:
        await fetch_snapshot(get_context())
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e.__class__.__name__ + ': ' + str(e))
        traceback.print_exc()
        send_alert(escape_markdown_v1(f"Snapshot task of {get_context().tenant} raised {e.__class__.__name__}\n {e}"))
    finally:
        tenant = get_context().tenant
        os.remove(LOG_PATH + f'/log_file_{tenant}.log')
        log_file = logging.FileHandler(f'log_file_{tenant}.log', 'w')
        log_file.setFormatter(formatter)
        logger.handlers.pop()
        logger.addHandler(log_file)


@app.task(trigger=OnStartUp())
async def startup():
    print(f"Starting up snapshot task for {get_context().tenant}")


@app.task(trigger=OnShutDown())
async def shutdown():
    print(f"Shutting down snapshot task for {get_context().tenant}")


if __name__ == "__main__":
    asyncio.run(app.serve())
