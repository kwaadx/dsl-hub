from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
from ..models.models import Thread, ThreadStatus, Message
from ..middleware.error import HTTPException

def list(db: Session, flow_id: Optional[str] = None, status: Optional[str] = None, archived: Optional[bool] = None, page: int = 1, page_size: int = 100) -> List[Thread]:
    """
    List threads with optional filters and pagination.
    """
    q = db.query(Thread)
    if flow_id:
        q = q.filter(Thread.flow_id == flow_id)
    if status:
        q = q.filter(Thread.status == status)
    if archived is not None:
        q = q.filter(Thread.archived.is_(archived))
    q = q.order_by(Thread.started_at.desc())
    offset = (page - 1) * page_size
    return q.offset(offset).limit(page_size).all()

def get(db: Session, thread_id: str) -> Optional[Thread]:
    """
    Get a thread by ID.
    """
    return db.query(Thread).filter(Thread.id == thread_id).first()

def remove(db: Session, thread_id: str) -> bool:
    """
    Remove a thread by ID.
    """
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        return False

    db.delete(thread)
    db.commit()

    return True

def archive(db: Session, thread_id: str) -> Optional[Thread]:
    """
    Archive a thread.
    """
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        return None

    thread.archived = True
    thread.archived_at = datetime.now()
    # Reflect archived state in status as well
    thread.status = ThreadStatus.ARCHIVED.value
    # Close the thread timestamp
    thread.closed_at = thread.closed_at or datetime.now()

    db.commit()
    db.refresh(thread)

    return thread

# ======================
# Messages helpers
# ======================
ALLOWED_ROLES = {"user", "assistant", "system", "tool"}
ALLOWED_FORMATS = {"text", "markdown", "json", "buttons", "card"}


def list_messages(db: Session, thread_id: str) -> List[Message]:
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, message="Thread not found")
    return (
        db.query(Message)
        .filter(Message.thread_id == thread_id)
        .order_by(Message.created_at.asc())
        .all()
    )


def create_message(db: Session, thread_id: str, msg_data: Dict[str, Any]) -> Message:
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, message="Thread not found")

    role = msg_data.role
    fmt = getattr(msg_data, "format", "text") or "text"
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, message=f"Invalid role: {role}")
    if fmt not in ALLOWED_FORMATS:
        raise HTTPException(status_code=400, message=f"Invalid format: {fmt}")
    if role == "tool" and not getattr(msg_data, "tool_name", None):
        raise HTTPException(status_code=400, message="tool_name is required when role=tool")

    parent_id = getattr(msg_data, "parent_id", None)
    if parent_id:
        parent = db.query(Message).filter(Message.id == parent_id).first()
        if not parent:
            raise HTTPException(status_code=400, message="parent_id not found")
        if parent.thread_id != thread_id:
            raise HTTPException(status_code=400, message="parent message must belong to the same thread")

    message_id = str(uuid.uuid4())
    message = Message(
        id=message_id,
        thread_id=thread_id,
        role=role,
        format=fmt,
        parent_id=parent_id,
        tool_name=getattr(msg_data, "tool_name", None),
        tool_result=getattr(msg_data, "tool_result", None),
        content=msg_data.content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)
    return message
