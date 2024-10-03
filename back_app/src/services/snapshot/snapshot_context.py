from dataclasses import dataclass

from multicallable import Multicallable
from sqlalchemy.orm import Session

from src.app.models import RuntimeConfiguration
from src.config.settings import Context


@dataclass
class SnapshotContext:
    context: Context
    session: Session
    config: RuntimeConfiguration
    multicallable: Multicallable
