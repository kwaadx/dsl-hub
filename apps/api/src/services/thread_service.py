from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import uuid
from sqlalchemy.orm import Session

from ..middleware.error import AppError
from ..models import Flow
from ..repositories.thread_repo import ThreadRepo

class ThreadService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ThreadRepo(db)

    def create(self, flow_id: str):
        if self.db.get(Flow, flow_id) is None:
            raise AppError(status=404, code="FLOW_NOT_FOUND", message="Flow not found")
        tid = str(uuid.uuid4())
        t = self.repo.create(tid, flow_id)
        return dict(id=str(t.id), flow_id=str(t.flow_id), status=t.status, started_at=t.started_at.isoformat())

    def list_for_flow(self, flow_id: str):
        if self.db.get(Flow, flow_id) is None:
            raise AppError(status=404, code="FLOW_NOT_FOUND", message="Flow not found")
        rows = self.repo.list_for_flow(flow_id)
        out = []
        for t in rows:
            out.append(dict(
                id=str(t.id),
                flow_id=str(t.flow_id),
                status=t.status,
                started_at=t.started_at.isoformat(),
                closed_at=t.closed_at.isoformat() if getattr(t, "closed_at", None) else None,
            ))
        return out
