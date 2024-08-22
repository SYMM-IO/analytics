from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from config.settings import Context
from utils.block import Block


def get_last_affiliate_snapshot_for(context: Context, session: Session, affiliate: str, hedger: str, block: Block):
    from app.models import AffiliateSnapshot

    return session.scalar(
        select(AffiliateSnapshot).where(
            and_(
                AffiliateSnapshot.tenant == context.tenant,
                AffiliateSnapshot.name == affiliate,
                AffiliateSnapshot.hedger_name == hedger,
                AffiliateSnapshot.block_number <= block.number,
            )
        ).order_by(
            AffiliateSnapshot.timestamp.desc()
        ).limit(1)
    )
