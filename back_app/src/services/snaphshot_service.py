from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from src.config.settings import Context
from src.utils.block import Block


def get_last_affiliate_snapshot_for(context: Context, session: Session, affiliate: str, hedger: str, block: Block):
    from src.app.models import AffiliateSnapshot

    return session.scalar(
        select(AffiliateSnapshot)
        .where(
            and_(
                AffiliateSnapshot.tenant == context.tenant,
                AffiliateSnapshot.name == affiliate,
                AffiliateSnapshot.hedger_name == hedger,
                AffiliateSnapshot.block_number <= block.number,
            )
        )
        .order_by(AffiliateSnapshot.timestamp.desc())
        .limit(1)
    )
