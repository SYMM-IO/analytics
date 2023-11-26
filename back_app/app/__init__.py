from playhouse.postgres_ext import PostgresqlExtDatabase

from config.settings import (
	db_name, db_user, db_password, db_host, db_port
)
from utils.logger_utils import setup_peewee_logger

pg_db = PostgresqlExtDatabase(db_name, user=db_user, password=db_password, host=db_host, port=db_port)
setup_peewee_logger()
