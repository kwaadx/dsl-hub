from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import FlowSummary


def get_active(db: Session, flow_id: str) -> Optional[FlowSummary]:
    """Return active FlowSummary for a flow, if any."""
    return db.execute(
        select(FlowSummary)
        .where(FlowSummary.flow_id == flow_id, FlowSummary.is_active == True)  # noqa: E712
        .limit(1)
    ).scalar_one_or_none()


def active_payload(fs: Optional[FlowSummary]) -> Dict[str, Any]:
    """Return API payload for an active flow summary (or default if missing)."""
    if not fs:
        return {"version": 0, "content": {}, "last_message_id": None}
    return {
        "version": fs.version,
        "content": fs.content,
        "last_message_id": str(fs.last_message_id) if fs.last_message_id else None,
    }
