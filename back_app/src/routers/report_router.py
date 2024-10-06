import os.path
from datetime import datetime
from time import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.responses import FileResponse

from src.app.scripts.aggregate_report import get_aggregate_report
from src.app.scripts.quotes_report import get_quotes_report
from src.config.local_settings import REPORTS_PATH

router = APIRouter(prefix="/report", tags=["Report"])


class ReportData(BaseModel):
    affiliate: str
    start: Optional[int] = None
    end: Optional[int] = None


@router.post("/quotes")
async def quotes_report_route(report_data: ReportData):
    affiliate = report_data.affiliate
    start = datetime.fromtimestamp(float(report_data.start or 0))
    end = datetime.fromtimestamp(float(report_data.end or time()))
    try:
        get_quotes_report(start, end, affiliate)
    except:
        raise HTTPException(status_code=400, detail='Bad request')
    if os.path.exists(file := f'{REPORTS_PATH}/{affiliate}_quotes.csv'):
        return FileResponse(file, media_type='application/octet-stream', filename=f'{affiliate}_quotes.csv')
    raise HTTPException(status_code=400, detail='Bad request')


@router.post("/aggregate")
async def aggregate_report_route(report_data: ReportData):
    affiliate = report_data.affiliate
    start = datetime.fromtimestamp(float(report_data.start or 0))
    end = datetime.fromtimestamp(float(report_data.end or time()))
    try:
        get_aggregate_report(start, end, affiliate)
    except:
        raise HTTPException(status_code=400, detail='Bad request')
    if os.path.exists(file := f'{REPORTS_PATH}/{affiliate}_aggregate.csv'):
        return FileResponse(file, media_type='application/octet-stream', filename=f'{affiliate}_aggregate.csv')
    raise HTTPException(status_code=400, detail='Bad request')
