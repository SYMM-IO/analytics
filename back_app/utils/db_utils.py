from contextlib import contextmanager

from app import pg_db
from app.models import BaseModel
from config.settings import Context


@contextmanager
def use_schema(context: Context):
	pg_db.execute_sql(f'CREATE SCHEMA IF NOT EXISTS "{context.tenant}";')
	models = BaseModel.__subclasses__()
	for model in models:
		model._meta.schema = context.tenant
	yield
