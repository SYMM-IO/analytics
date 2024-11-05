from fastapi import APIRouter, Path, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, aliased

from src.app import get_db_session
from src.app.models import User
from src.app.subgraph_models import Account, TradeHistory
from src.app.response_models import UserTradingVolume

router = APIRouter(prefix="/user-history", tags=["User History"])


@router.get("/trading-volume/{tenant}/{address}", response_model=UserTradingVolume)
async def get_user_trading_volume(
    tenant: str = Path(..., description="The tenant of this user"),
    address: str = Path(..., description="Address of the user"),
    session: Session = Depends(get_db_session),
):
    # Construct the user ID
    user_id = f"{tenant}_{address}"

    # Create aliases for the joined tables
    user_alias = aliased(User)
    account_alias = aliased(Account)
    trade_history_alias = aliased(TradeHistory)

    # Construct the query
    query = (
        select(func.sum(trade_history_alias.volume).label("total_volume"))
        .select_from(user_alias)
        .join(account_alias, user_alias.id == account_alias.user_id)
        .join(trade_history_alias, account_alias.id == trade_history_alias.account_id)
        .where(
            and_(
                user_alias.tenant == tenant,
                user_alias.id == user_id,
            )
        )
    )

    # Execute the query
    result = session.execute(query).scalar_one_or_none()

    # Prepare the response
    total_volume = float(result) if result is not None else 0.0

    return {"user_id": user_id, "tenant": tenant, "address": address, "total_trading_volume": total_volume}
