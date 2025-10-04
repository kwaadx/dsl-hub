from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..services.thread_service import ThreadService
from ..services.message_service import MessageService
from ..dto import ThreadOut, MessageIn, MessageOut
from ..models import Thread

router = APIRouter(prefix="/threads", tags=["threads"]) 

@router.post("/by-flow/{flow_id}", response_model=ThreadOut, status_code=201, deprecated=True)
def create_thread(flow_id: str, response: Response, db: Session = Depends(get_db)):
    # Deprecated: use POST /flows/{flow_id}/threads
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = "</flows/{flow_id}/threads>; rel=successor-version"
    svc = ThreadService(db)
    return svc.create(flow_id)

@router.get("/{thread_id}", response_model=ThreadOut)
def get_thread(thread_id: str, db: Session = Depends(get_db)):
    # Minimal metadata (extend as needed)
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    return {
        "id": thread_id,
        "flow_id": str(t.flow_id),
        "status": t.status,
        "started_at": t.started_at.isoformat() if isinstance(t.started_at, datetime) else str(t.started_at),
        "closed_at": t.closed_at.isoformat() if getattr(t, "closed_at", None) else None,
    }

@router.get("/{thread_id}/messages")
def list_messages(thread_id: str, limit: int = 50, before: str | None = None, db: Session = Depends(get_db)):
    svc = MessageService(db)
    return svc.list(thread_id, limit=limit, before=before)

@router.post("/{thread_id}/messages", response_model=MessageOut, status_code=201)
def add_message(thread_id: str, payload: MessageIn, db: Session = Depends(get_db)):
    svc = MessageService(db)
    # Let AppError bubble up to the global error handler for unified error shape
    return svc.add(
        thread_id,
        payload.role,
        payload.content,
        payload.parent_id,
        payload.tool_name,
        payload.tool_result,
        fmt=payload.format or "text",
    )

@router.post("/{thread_id}/close")
async def close_thread(thread_id: str, db: Session = Depends(get_db)):
    from ..services.summary_service import SummaryService
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    svc = SummaryService(db)
    # Delegate to service to ensure atomicity and single-source computations
    return await svc.close_thread(thread_id)

@router.get("/{thread_id}/summaries")
def get_thread_summaries(thread_id: str, db: Session = Depends(get_db)):
    from ..repositories.thread_summary_repo import list_for_thread, payload as ts_payload
    rows = list_for_thread(db, thread_id)
    return [ts_payload(r) for r in rows]
