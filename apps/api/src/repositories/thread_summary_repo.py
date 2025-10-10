from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import ThreadSummary


def list_for_thread(db: Session, thread_id: str) -> List[ThreadSummary]:
    """Return thread summaries for a given thread, newest first."""
    return list(
        db.execute(
            select(ThreadSummary)
            .where(ThreadSummary.thread_id == thread_id)
            .order_by(ThreadSummary.created_at.desc())
        ).scalars().all()
    )


def create(db: Session, thread_id: str, *, kind: str, content: Dict[str, Any], token_budget: int,
           covering_from: Optional[datetime], covering_to: Optional[datetime]) -> ThreadSummary:
    ts = ThreadSummary(
        id=str(uuid.uuid4()),
        thread_id=thread_id,
        kind=kind,
        content=content,
        token_budget=token_budget,
        covering_from=covering_from,
        covering_to=covering_to,
    )
    db.add(ts)
    db.flush()
    db.refresh(ts)
    return ts


def payload(ts: ThreadSummary) -> Dict[str, Any]:
    """Standard API payload for a ThreadSummary row."""
    return dict(
        id=str(ts.id),
        kind=ts.kind,
        content=ts.content,
        covering_from=ts.covering_from.isoformat() if ts.covering_from else None,
        covering_to=ts.covering_to.isoformat() if ts.covering_to else None,
    )
