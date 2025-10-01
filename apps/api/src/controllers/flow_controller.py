from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
from ..models.models import Flow, Thread, ThreadStatus
from ..middleware.error import HTTPException

def list(db: Session) -> List[Flow]:
    """
    List all flows.
    """
    return db.query(Flow).all()

def create(db: Session, flow_data: Dict[str, Any]) -> Flow:
    """
    Create a new flow.
    """
    # Generate a unique ID
    flow_id = str(uuid.uuid4())

    # Use provided name or generate a default name
    name = flow_data.name if flow_data.name else f"Flow {datetime.now().timestamp()}"

    # Create flow
    flow = Flow(id=flow_id, name=name)

    # Save to database
    db.add(flow)
    db.commit()
    db.refresh(flow)

    return flow

def get(db: Session, flow_id: str) -> Optional[Flow]:
    """
    Get a flow by ID.
    """
    return db.query(Flow).filter(Flow.id == flow_id).first()

def remove(db: Session, flow_id: str) -> bool:
    """
    Remove a flow by ID.
    """
    flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not flow:
        return False

    db.delete(flow)
    db.commit()

    return True

def new_or_active_thread(db: Session, flow_id: str) -> Thread:
    """
    Create a new thread or get an active thread for a flow.
    """
    # Check if flow exists
    flow = db.query(Flow).filter(Flow.id == flow_id).first()
    if not flow:
        raise HTTPException(status_code=404, message="Flow not found")

    # Look for an active thread
    active_thread = db.query(Thread).filter(
        Thread.flow_id == flow_id,
        Thread.status.in_([ThreadStatus.NEW, ThreadStatus.IN_PROGRESS]),
        Thread.archived == False
    ).first()

    if active_thread:
        return active_thread

    # Create a new thread
    thread_id = str(uuid.uuid4())
    thread = Thread(
        id=thread_id,
        flow_id=flow_id,
        status=ThreadStatus.NEW
    )

    db.add(thread)
    db.commit()
    db.refresh(thread)

    return thread
