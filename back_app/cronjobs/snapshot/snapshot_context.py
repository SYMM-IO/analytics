from dataclasses import dataclass

import web3
from sqlalchemy.orm import Session

from app.models import RuntimeConfiguration
from config.settings import Context


@dataclass
class SnapshotContext:
    context: Context
    session: Session
    config: RuntimeConfiguration
    w3: web3.Web3
