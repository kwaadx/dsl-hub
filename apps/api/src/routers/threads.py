from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.thread_service import ThreadService
from ..services.message_service import MessageService
from ..dto import CreateThread, ThreadOut, MessageIn, MessageOut

router = APIRouter(prefix="/threads", tags=["threads"])

@router.post("/by-flow/{flow_id}", response_model=ThreadOut, status_code=201)
def create_thread(flow_id: str, db: Session = Depends(get_db)):
    svc = ThreadService(db)
    return svc.create(flow_id)

@router.get("/{thread_id}")
def get_thread(thread_id: str, db: Session = Depends(get_db)):
    # Minimal metadata (extend as needed)
    from ..models import Thread
    t = db.get(Thread, thread_id)
    if not t:
        raise HTTPException(404, "Thread not found")
    return {"id": thread_id, "flow_id": str(t.flow_id), "status": t.status, "started_at": t.started_at}

@router.get("/{thread_id}/messages")
def list_messages(thread_id: str, limit: int = 50, db: Session = Depends(get_db)):
    svc = MessageService(db)
    return svc.list(thread_id, limit=limit)

@router.post("/{thread_id}/messages", response_model=MessageOut, status_code=201)
def add_message(thread_id: str, payload: MessageIn, db: Session = Depends(get_db)):
    svc = MessageService(db)
    return svc.add(thread_id, payload.role, payload.content, payload.parent_id, payload.tool_name, payload.tool_result)
