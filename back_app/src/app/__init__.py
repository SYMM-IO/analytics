from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, text, bindparam, String
from sqlalchemy.orm import sessionmaker, Session

from src.app.models import BaseModel, LogSpan, LogTransaction
from src.config.local_settings import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Define the database connection URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create an Engine with a connection pool
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def db_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


@contextmanager
def log_span_context(session: Session, label: str, transaction_id: int):
    span = LogSpan(start_time=datetime.now(), label=label, transaction_id=transaction_id)
    try:
        yield span
    finally:
        span.end_time = datetime.now()
        span.save(session)
        session.commit()


@contextmanager
def log_transaction_context(session: Session, label: str, tenant: str):
    tx = LogTransaction(start_time=datetime.now(), label=label, tenant=tenant)
    tx.save(session)
    session.commit()
    try:
        yield tx
    finally:
        tx.end_time = datetime.now()
        tx.save(session)
        session.commit()


def get_db_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def is_hyper_table(session: Session, table_name):
    query = f"""
        SELECT * FROM timescaledb_information.hypertable
        WHERE table_name = '{table_name}';
        """
    result = session.execute(query)
    hypertable_info = result.fetchall()
    return hypertable_info is not None


def create_hyper_tables_read_write_permissions():
    with db_session() as session:
        for model in BaseModel.__subclasses__():
            if model.__is_timeseries__:
                if not is_hyper_table(session, model.__tablename__):
                    hypertable_query = text("SELECT create_hypertable(:table_name, 'timestamp')")
                    hypertable_query = hypertable_query.bindparams(bindparam("table_name", type_=String))
                    session.execute(hypertable_query, {"table_name": model.__tablename__})
