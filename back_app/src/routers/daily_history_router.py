from datetime import datetime, timedelta
from threading import Lock
from typing import List, Dict

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.app import log_transaction_context, db_session
from src.app.response_models import DailyHistoryAffiliate
from src.app.subgraph_models import DailyHistory, WeeklyHistory, MonthlyHistory, SolverDailyHistory, TotalHistory
from src.config.local_settings import contexts
from src.config.settings import UPDATE_HISTORIES_INTERVAL
from src.utils.block import Block
from src.utils.subgraph.subgraph_client import SubgraphClient

router = APIRouter(prefix="/history", tags=["Daily History"])

last_execution_time = datetime.now() - timedelta(days=1000)
lock = Lock()


def prepare_data(session: Session):
    global last_execution_time
    with lock:
        now = datetime.now()
        if now - last_execution_time > timedelta(seconds=UPDATE_HISTORIES_INTERVAL):
            for context in contexts:
                with log_transaction_context(session, "prepareData", context.tenant) as log_tx:
                    subgraph_client = SubgraphClient(context)
                    sync_block = Block.latest(context.w3)
                    subgraph_client.sync(
                        session, sync_block, log_tx.id, [DailyHistory, WeeklyHistory, MonthlyHistory, SolverDailyHistory, TotalHistory]
                    )
            last_execution_time = now
            return


@router.get("/daily/{group_by}", response_model=Dict[str, List[DailyHistoryAffiliate]])
async def get_aggregate_affiliates_history(group_by="day", session: Session = Depends(db_session)):
    if group_by not in ["day", "week", "month"]:
        raise HTTPException(status_code=404, detail="Not found")
    prepare_data(session)
    # TODO: Prepare daily aggregates
