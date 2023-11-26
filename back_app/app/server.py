from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS
from flask_restx import Api

from config.local_settings import contexts
from config.settings import (
    server_port,
    fetch_data_interval,
    fetch_stat_data_interval,
    update_binance_deposit_interval,
)
from context.migrations import create_tables
from cronjobs import load_stats_messages
from cronjobs.aggregate_data_job import fetch_aggregate_data
from namespaces import config_namespace
from utils.binance_utils import update_binance_deposit_v2
from utils.telegram_utils import send_alert, escape_markdown_v1

scheduler: BackgroundScheduler


def create_schedular():
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_listener(listener, EVENT_JOB_ERROR)
    for context in contexts:
        scheduler.add_job(
            func=lambda: load_stats_messages(context),
            trigger="interval",
            seconds=fetch_stat_data_interval,
        )
        scheduler.add_job(
            func=lambda: fetch_aggregate_data(context),
            trigger="interval",
            seconds=fetch_data_interval,
        )
        scheduler.add_job(
            func=lambda: update_binance_deposit_v2(context),
            trigger="interval",
            seconds=update_binance_deposit_interval,
        )
        # scheduler.add_job(
        # 	func=lambda: calculate_paid_funding(context),
        # 	trigger="interval",
        # 	seconds=funding_fetch_data_interval
        # )
        # scheduler.add_job(
        # 	func=lambda: update_binance_deposit(context),
        # 	trigger="interval",
        # 	seconds=update_binance_deposit_interval
        # )
    scheduler.start()


def listener(event):
    global scheduler
    send_alert(
        escape_markdown_v1(
            f"BackgroundJob {event.job_id} raised {event.exception.__class__.__name__}\n {event.exception}"
        )
    )
    scheduler.shutdown(wait=False)
    create_schedular()


app = Flask(__name__)
api = Api(app, validate=True)

api.add_namespace(config_namespace.ns, path="/configs")
CORS(app, resources={r"*": {"origins": "*"}})

create_tables()

create_schedular()

if __name__ == "__main__":
    app.run(port=server_port, debug=True, use_reloader=False)
