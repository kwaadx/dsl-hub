from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
from datetime import datetime
from ..models.models import Thread, ThreadStatus
from ..middleware.error import HTTPException

def list(db: Session) -> List[Thread]:
    """
    List all threads.
    """
    return db.query(Thread).all()

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

    db.commit()
    db.refresh(thread)

    return thread
