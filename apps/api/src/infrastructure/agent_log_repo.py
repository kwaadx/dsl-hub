from __future__ import annotations

from sqlalchemy.orm import Session
from ..models import AgentLog
from ..core.ports import AgentLogRepo
from uuid import uuid4

class SAAgentLogRepo(AgentLogRepo):
    def __init__(self, db: Session): self.db = db
    def write(self, run_id: str, thread_id: str, flow_id: str, step: str, level: str, message: str, data: dict | None = None) -> None:
        row = AgentLog(id=str(uuid4()), run_id=run_id, thread_id=thread_id, flow_id=flow_id, step=step, level=level, message=message, data=data or {})
        self.db.add(row)