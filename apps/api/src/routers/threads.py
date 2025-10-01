from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from ..database import get_db
from ..services.thread_service import ThreadService
from ..services.message_service import MessageService
from ..services.pipeline_service import PipelineService
from ..dto import CreateThread, ThreadOut, MessageIn, MessageOut
from ..models import Thread, ThreadSummary, FlowSummary

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
        return svc.add(thread_id, payload.role, payload.content, payload.parent_id, payload.tool_name, payload.tool_result, payload.format or "text")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{thread_id}/close")
def close_thread(thread_id: str, db: Session = Depends(get_db)):
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    # create minimal thread summary
    ts = ThreadSummary(id=str(__import__('uuid').uuid4()), thread_id=thread_id, kind="short", content={"summary": "Thread closed"})
    db.add(ts)
    # upsert active flow summary
    fs = db.execute(select(FlowSummary).where(FlowSummary.flow_id==t.flow_id, FlowSummary.is_active==True).limit(1)).scalar_one_or_none()
    if fs:
        fs.version = (fs.version or 0) + 1
        fs.content = {"summary": "Updated by thread close"}
        fs.is_active = True
    else:
        fs = FlowSummary(id=str(__import__('uuid').uuid4()), flow_id=t.flow_id, version=1, content={"summary": "Initial"}, is_active=True)
        db.add(fs)
    t.status = "SUCCESS"
    t.closed_at = datetime.utcnow()
    db.flush()
    return {"ok": True}

@router.get("/{thread_id}/summaries")
def get_thread_summaries(thread_id: str, db: Session = Depends(get_db)):
    rows = db.execute(select(ThreadSummary).where(ThreadSummary.thread_id==thread_id).order_by(ThreadSummary.created_at.desc())).scalars().all()
    return [{
        "id": str(r.id), "kind": r.kind, "content": r.content,
        "covering_from": r.covering_from.isoformat() if r.covering_from else None,
        "covering_to": r.covering_to.isoformat() if r.covering_to else None
    } for r in rows]
