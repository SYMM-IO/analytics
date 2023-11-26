from app import pg_db
from app.models import BaseModel


def create_tables():
    models = BaseModel.__subclasses__()
    for model in models:
        model.create_table()
        if model.is_timeseries() and not model.table_exists():
            pg_db.execute_sql(
                f"SELECT create_hypertable('{model.__name__}', 'timestamp');"
            )
