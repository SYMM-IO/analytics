import os.path
import subprocess
from time import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.responses import FileResponse

from src.config.local_settings import SCRIPTS_PATH, REPORTS_PATH

router = APIRouter(prefix="/report", tags=["Report"])


class ReportData(BaseModel):
    affiliate: str
    start: Optional[int] = None
    end: Optional[int] = None


@router.post("/quotes")
async def get_quotes_report(report_data: ReportData):
    affiliate = report_data.affiliate
    start = report_data.start
    end = report_data.end
    process = subprocess.run(
        f'start={start or 0} end={end or time()} affiliate={affiliate} python3 {SCRIPTS_PATH}/quotes_report.py',
        shell=True)
    if process.returncode == 0 and os.path.exists(file := f'{REPORTS_PATH}/{affiliate}_quotes.csv'):
        return FileResponse(file, media_type='application/octet-stream', filename=f'{affiliate}_quotes.csv')
    raise HTTPException(status_code=400, detail='Bad request')


@router.post("/aggregate")
async def get_aggregate_report(report_data: ReportData):
    affiliate = report_data.affiliate
    start = report_data.start
    end = report_data.end
    process = subprocess.run(
        f'start={start or 0} end={end or time()} affiliate={affiliate} python3 {SCRIPTS_PATH}/aggregate_report.py',
        shell=True)
    if process.returncode == 0 and os.path.exists(file := f'{REPORTS_PATH}/{affiliate}_aggregate.csv'):
        return FileResponse(file, media_type='application/octet-stream', filename=f'{affiliate}_aggregate.csv')
    raise HTTPException(status_code=400, detail='Bad request')
