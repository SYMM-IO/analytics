"""load_parties

Revision ID: 260704edd4ae
Revises: 5b2b4ae63904
Create Date: 2024-11-05 09:27:33.323470

"""

from typing import Sequence, Union

from src.app import db_session
from src.app.models import Affiliate, Solver
from src.config.local_settings import contexts

# revision identifiers, used by Alembic.
revision: str = "260704edd4ae"
down_revision: Union[str, None] = "5b2b4ae63904"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with db_session() as session:
        for context in contexts:
            for affiliate in context.affiliates:
                aff_model = Affiliate(id=affiliate.symmio_multi_account, name=affiliate.name, tenant=context.tenant)
                aff_model.upsert(session)
            for solver in context.hedgers:
                solver_model = Solver(id=solver.hedger_address, name=solver.name, tenant=context.tenant)
                solver_model.upsert(session)


def downgrade() -> None:
    pass
