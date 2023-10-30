from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS
from flask_restx import Api

from config.settings import server_port, fetch_data_interval, funding_fetch_data_interval
from context.migrations import create_tables
from cronjobs.aggregate_data_job import fetch_aggregate_data
from cronjobs.paid_funding_job import calculate_paid_funding
from namespaces import config_namespace
from utils.telegram_utils import send_alert, escape_markdown_v1

scheduler: BackgroundScheduler = None

def create_schedular():
    global scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=fetch_aggregate_data, trigger="interval", seconds=fetch_data_interval)
    scheduler.add_job(func=calculate_paid_funding, trigger="interval", seconds=funding_fetch_data_interval)
    # scheduler.add_job(func=update_binance_deposit, trigger="interval", seconds=update_binance_deposit_interval)
    scheduler.add_listener(listener, EVENT_JOB_ERROR)
    scheduler.start()


def listener(event):
    global scheduler
    send_alert(
        escape_markdown_v1(
            f'BackgroundJob {event.job_id} raised {event.exception.__class__.__name__}\n {event.exception}'))
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
