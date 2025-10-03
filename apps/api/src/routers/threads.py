from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, UTC
import uuid
from ..database import get_db
from ..services.thread_service import ThreadService
from ..services.message_service import MessageService
from ..dto import ThreadOut, MessageIn, MessageOut
from ..models import Thread, ThreadSummary, FlowSummary, Message

router = APIRouter(prefix="/threads", tags=["threads"])

@router.post("/by-flow/{flow_id}", response_model=ThreadOut, status_code=201)
def create_thread(flow_id: str, db: Session = Depends(get_db)):
    svc = ThreadService(db)
    return svc.create(flow_id)

@router.get("/{thread_id}")
def get_thread(thread_id: str, db: Session = Depends(get_db)):
    # Minimal metadata (extend as needed)
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    return {"id": thread_id, "flow_id": str(t.flow_id), "status": t.status, "started_at": t.started_at}

@router.get("/{thread_id}/messages")
def list_messages(thread_id: str, limit: int = 50, before: str | None = None, db: Session = Depends(get_db)):
    svc = MessageService(db)
    return svc.list(thread_id, limit=limit, before=before)

@router.post("/{thread_id}/messages", response_model=MessageOut, status_code=201)
def add_message(thread_id: str, payload: MessageIn, db: Session = Depends(get_db)):
    svc = MessageService(db)
    try:
        return svc.add(thread_id, payload.role, payload.content, payload.parent_id, payload.tool_name, payload.tool_result, fmt=payload.format or "text")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{thread_id}/close")
async def close_thread(thread_id: str, db: Session = Depends(get_db)):
    from ..services.summary_service import SummaryService
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    svc = SummaryService(db)
    # Generate thread summary (async LLM call)
    ts = await svc.run_thread_summary(thread_id)
    # Determine last message id for flow summary linking
    from sqlalchemy import select as _select
    last_msg = db.execute(
        _select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at.desc()).limit(1)
    ).scalar_one_or_none()
    last_message_id = str(last_msg.id) if last_msg else None
    # Upsert active flow summary and ensure single active
    fs = svc.upsert_flow_summary(str(t.flow_id), last_message_id=last_message_id, new_content={"summary": ts.content.get("summary", "")})
    svc.ensure_single_active(str(t.flow_id), str(fs.id))
    # Close thread
    t.status = "SUCCESS"
    t.closed_at = datetime.now(UTC)
    db.flush()
    return {"ok": True, "thread_id": thread_id, "thread_summary_id": str(ts.id), "flow_summary": {"id": str(fs.id), "version": fs.version}}

@router.get("/{thread_id}/summaries")
def get_thread_summaries(thread_id: str, db: Session = Depends(get_db)):
    from ..repositories.thread_summary_repo import list_for_thread, payload as ts_payload
    rows = list_for_thread(db, thread_id)
    return [ts_payload(r) for r in rows]
