from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from ..models.database import get_db
from ..models.models import AgentLog

router = APIRouter()

class AgentLogItem(BaseModel):
    id: str
    flow_id: Optional[str] = None
    thread_id: Optional[str] = None
    level: str
    event: str
    data: Optional[dict] = None
    created_at: str

    class Config:
        orm_mode = True

class Paged(BaseModel):
    items: List[AgentLogItem]
    page: int
    pageSize: int
    totalItems: int
    totalPages: int

@router.get("/", response_model=Paged)
async def list_logs(
    db: Session = Depends(get_db),
    flow_id: Optional[str] = Query(None),
    thread_id: Optional[str] = Query(None),
    level: Optional[str] = Query(None, description="debug|info|warn|error"),
    from_ts: Optional[str] = Query(None, alias="from"),
    to_ts: Optional[str] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=500),
):
    q = db.query(AgentLog)
    if flow_id:
        q = q.filter(AgentLog.flow_id == flow_id)
    if thread_id:
        q = q.filter(AgentLog.thread_id == thread_id)
    if level:
        q = q.filter(AgentLog.level == level)
    if from_ts:
        # Rely on Postgres to parse ISO8601 timestamp string
        q = q.filter(AgentLog.created_at >= from_ts)
    if to_ts:
        q = q.filter(AgentLog.created_at <= to_ts)

    total = q.count()
    q = q.order_by(AgentLog.created_at.desc())

    offset = (page - 1) * pageSize
    items = q.offset(offset).limit(pageSize).all()
    total_pages = (total + pageSize - 1) // pageSize if total > 0 else 1

    return {
        "items": items,
        "page": page,
        "pageSize": pageSize,
        "totalItems": total,
        "totalPages": total_pages,
    }
