from __future__ import annotations
from typing import Any, Dict, List
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


def payload(ts: ThreadSummary) -> Dict[str, Any]:
    """Standard API payload for a ThreadSummary row."""
    return dict(
        id=str(ts.id),
        kind=ts.kind,
        content=ts.content,
        covering_from=ts.covering_from.isoformat() if ts.covering_from else None,
        covering_to=ts.covering_to.isoformat() if ts.covering_to else None,
    )
