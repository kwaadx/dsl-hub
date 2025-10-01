from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import re
from sqlalchemy import or_

from ..models.models import Flow, Thread, ThreadStatus
from ..middleware.error import HTTPException

def list(db: Session, q: Optional[str] = None, page: int = 1, page_size: int = 100) -> list[type[Flow]]:
    """
    List flows with optional search and pagination.
    """
    query = db.query(Flow)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Flow.name.ilike(like), Flow.slug.ilike(like)))
    query = query.order_by(Flow.created_at.desc())
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size).all()

def _slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or f"flow-{uuid.uuid4().hex[:8]}"

def create(db: Session, flow_data: Dict[str, Any]) -> Flow:
    """
    Create a new flow.
    """
    flow_id = str(uuid.uuid4())
    name = flow_data.name if getattr(flow_data, "name", None) else f"Flow {int(datetime.now().timestamp())}"

    base_slug = getattr(flow_data, "slug", None) or _slugify(name)
    slug = base_slug
    i = 1
    while db.query(Flow).filter(Flow.slug == slug).first() is not None:
        slug = f"{base_slug}-{i}"
        i += 1

    flow = Flow(id=flow_id, name=name, slug=slug, meta={})
    db.add(flow)
    db.commit()
    db.refresh(flow)

    return flow

def update(db: Session, flow_id: str, patch: Dict[str, Any]) -> Optional[Flow]:
    flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not flow:
        return None

    new_name = getattr(patch, "name", None)
    new_slug = getattr(patch, "slug", None)

    if new_name and not new_slug:
        # Update slug from name if slug not explicitly provided
        new_slug = _slugify(new_name)

    if new_slug and new_slug != flow.slug:
        base_slug = new_slug
        slug = base_slug
        i = 1
        while db.query(Flow).filter(Flow.slug == slug, Flow.id != flow_id).first() is not None:
            slug = f"{base_slug}-{i}"
            i += 1
        flow.slug = slug

    if new_name:
        flow.name = new_name

    db.commit()
    db.refresh(flow)
    return flow

def get(db: Session, flow_id: str) -> Optional[Flow]:
    return db.query(Flow).filter(Flow.id == flow_id).first()

def remove(db: Session, flow_id: str) -> bool:
    flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not flow:
        return False

    db.delete(flow)
    db.commit()

    return True

def new_or_active_thread(db: Session, flow_id: str) -> Thread:
    flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, message="Flow not found")

    active_thread = db.query(Thread).filter(
        Thread.flow_id == flow_id,
        Thread.status.in_([ThreadStatus.NEW.value, ThreadStatus.IN_PROGRESS.value]),
        Thread.archived == False
    ).first()

    if active_thread:
        return active_thread

    thread_id = str(uuid.uuid4())
    thread = Thread(
        id=thread_id,
        flow_id=flow_id,
        status=ThreadStatus.NEW.value
    )

    db.add(thread)
    db.commit()
    db.refresh(thread)

    return thread
