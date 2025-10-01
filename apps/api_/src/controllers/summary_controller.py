from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import uuid
from ..models.models import FlowSummary, ThreadSummary
from ..middleware.error import HTTPException

# -------- Flow Summaries --------

def list_flow_summaries(
    db: Session,
    flow_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    version: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
):
    q = db.query(FlowSummary)
    if flow_id:
        q = q.filter(FlowSummary.flow_id == flow_id)
    if is_active is not None:
        q = q.filter(FlowSummary.is_active.is_(is_active))
    if version is not None:
        q = q.filter(FlowSummary.version == version)

    total = q.count()
    q = q.order_by(FlowSummary.created_at.desc())
    offset = (page - 1) * page_size
    items = q.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "totalItems": total,
        "totalPages": total_pages,
    }


def create_flow_summary(db: Session, data) -> FlowSummary:
    # Compute next version for flow
    max_ver = (
        db.query(func.max(FlowSummary.version)).filter(FlowSummary.flow_id == data.flow_id).scalar()
        or 0
    )
    new_ver = max_ver + 1

    fs = FlowSummary(
        id=str(uuid.uuid4()),
        flow_id=data.flow_id,
        version=new_ver,
        content=data.content,
        pinned=getattr(data, "pinned", {}) or {},
        last_message_id=getattr(data, "last_message_id", None),
        is_active=bool(getattr(data, "is_active", False)),
    )

    db.add(fs)
    db.commit()
    db.refresh(fs)

    # If requested active, deactivate others (friendly; DB enforces unique partial index)
    if fs.is_active:
        db.query(FlowSummary).filter(
            FlowSummary.flow_id == fs.flow_id,
            FlowSummary.id != fs.id,
            FlowSummary.is_active.is_(True),
        ).update({FlowSummary.is_active: False})
        db.commit()
        db.refresh(fs)

    return fs


def activate_flow_summary(db: Session, fs_id: str) -> Optional[FlowSummary]:
    fs = db.query(FlowSummary).filter(FlowSummary.id == fs_id).first()
    if not fs:
        return None

    # Deactivate others and activate this one
    db.query(FlowSummary).filter(
        FlowSummary.flow_id == fs.flow_id,
        FlowSummary.id != fs.id,
        FlowSummary.is_active.is_(True),
    ).update({FlowSummary.is_active: False})

    fs.is_active = True
    db.commit()
    db.refresh(fs)
    return fs


def get_flow_summary(db: Session, fs_id: str) -> Optional[FlowSummary]:
    return db.query(FlowSummary).filter(FlowSummary.id == fs_id).first()

# -------- Thread Summaries --------

def list_thread_summaries(
    db: Session,
    thread_id: Optional[str] = None,
    kind: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    q = db.query(ThreadSummary)
    if thread_id:
        q = q.filter(ThreadSummary.thread_id == thread_id)
    if kind:
        q = q.filter(ThreadSummary.kind == kind)

    total = q.count()
    q = q.order_by(ThreadSummary.created_at.desc())
    offset = (page - 1) * page_size
    items = q.offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "totalItems": total,
        "totalPages": total_pages,
    }


def create_thread_summary(db: Session, data) -> ThreadSummary:
    ts = ThreadSummary(
        id=str(uuid.uuid4()),
        thread_id=data.thread_id,
        kind=getattr(data, "kind", "short") or "short",
        content=data.content,
        token_budget=getattr(data, "token_budget", 1024) or 1024,
        covering_from=getattr(data, "covering_from", None),
        covering_to=getattr(data, "covering_to", None),
    )

    db.add(ts)
    db.commit()
    db.refresh(ts)
    return ts


def get_thread_summary(db: Session, ts_id: str) -> Optional[ThreadSummary]:
    return db.query(ThreadSummary).filter(ThreadSummary.id == ts_id).first()
