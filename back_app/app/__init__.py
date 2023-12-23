from playhouse.postgres_ext import PostgresqlExtDatabase

from config.settings import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from utils.logger_utils import setup_peewee_logger

pg_db = PostgresqlExtDatabase(
    DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
setup_peewee_logger()
