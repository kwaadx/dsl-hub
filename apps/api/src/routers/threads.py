from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import db_session  # legacy DI
from ..deps import uc_get_thread
from sqlalchemy.orm import Session
from ..dto import ThreadOut, MessageIn, MessageOut
from ..middleware.error import AppError
from ..models import Thread
from ..services.message_service import MessageService

router = APIRouter(prefix="/threads", tags=["threads"]) 


@router.get("/{thread_id}", response_model=ThreadOut)
def get_thread(thread_id: str, db: Session = Depends(db_session)) -> ThreadOut:
    # Minimal metadata (extend as needed)
    t = db.get(Thread, thread_id)
    if not t:
        raise AppError(status=404, code="THREAD_NOT_FOUND", message="Thread not found")
    payload = dict(
        id=thread_id,
        flow_id=str(t.flow_id),
        status=t.status,
        started_at=t.started_at.isoformat() if isinstance(t.started_at, datetime) else str(t.started_at),
        closed_at=t.closed_at.isoformat() if getattr(t, "closed_at", None) else None,
    )
    return ThreadOut(**payload)

@router.get("/{thread_id}/messages")
def list_messages(thread_id: str, limit: int = 50, before: str | None = None, db: Session = Depends(db_session)) -> List[Dict[str, Any]]:
    svc = MessageService(db)
    return svc.list(thread_id, limit=limit, before=before)

@router.post("/{thread_id}/messages", response_model=MessageOut, status_code=201)
def add_message(thread_id: str, payload: MessageIn, db: Session = Depends(db_session)) -> MessageOut:
    svc = MessageService(db)
    # Let AppError bubble up to the global error handler for unified error shape
    result = svc.add(
        thread_id,
        payload.role,
        payload.content,
        payload.parent_id,
        payload.tool_name,
        payload.tool_result,
        fmt=payload.format or "text",
    )
    return MessageOut(**result)

@router.post("/{thread_id}/close")
async def close_thread(thread_id: str, db: Session = Depends(db_session)) -> Dict[str, Any]:
    from ..services.summary_service import SummaryService
    svc = SummaryService(db)
    # Delegate to service to ensure atomicity and single-source computations
    return await svc.close_thread(thread_id)

@router.get("/{thread_id}/summaries")
def get_thread_summaries(thread_id: str, db: Session = Depends(db_session)) -> List[Dict[str, Any]]:
    from ..repositories.thread_summary_repo import list_for_thread, payload as ts_payload
    rows = list_for_thread(db, thread_id)
    return [ts_payload(r) for r in rows]
