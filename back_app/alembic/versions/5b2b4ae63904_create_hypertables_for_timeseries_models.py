"""create HyperTables for timeseries models

Revision ID: 5b2b4ae63904
Revises: f84afbd6c9a6
Create Date: 2024-03-06 14:06:48.155508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

from app.models import BaseModel

# revision identifiers, used by Alembic.
revision: str = '5b2b4ae63904'
down_revision: Union[str, None] = 'f84afbd6c9a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Bind the Alembic Connection to your SQLAlchemy engine
    bind = op.get_bind()

    for model in BaseModel.__subclasses__():
        if model.__is_timeseries__:
            hypertable_query = text("SELECT create_hypertable(:table_name, 'timestamp')")
            hypertable_query = hypertable_query.bindparams(sa.bindparam('table_name', type_=sa.String))

            bind.execute(hypertable_query, { 'table_name': model.__tablename__ })


def downgrade() -> None:
    pass
