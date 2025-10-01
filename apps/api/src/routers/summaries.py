from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import FlowSummary, ThreadSummary

router = APIRouter(prefix="/summaries", tags=["summaries"])

@router.get("/flow/{flow_id}/active")
def get_flow_active(flow_id: str, db: Session = Depends(get_db)):
    fs = db.execute(select(FlowSummary).where(FlowSummary.flow_id==flow_id, FlowSummary.is_active==True).limit(1)).scalar_one_or_none()
    if not fs:
        return {"version": 0, "content": {}, "last_message_id": None}
    return {"version": fs.version, "content": fs.content, "last_message_id": str(fs.last_message_id) if fs.last_message_id else None}

@router.get("/thread/{thread_id}")
def list_thread_summaries(thread_id: str, db: Session = Depends(get_db)):
    rows = db.execute(select(ThreadSummary).where(ThreadSummary.thread_id==thread_id).order_by(ThreadSummary.created_at.desc())).scalars().all()
    return [{
        "id": str(r.id), "kind": r.kind, "content": r.content,
        "covering_from": r.covering_from.isoformat() if r.covering_from else None,
        "covering_to": r.covering_to.isoformat() if r.covering_to else None
    } for r in rows]
