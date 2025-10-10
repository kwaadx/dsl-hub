from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from ..deps import agent_log
from ..models import AgentLog
from sqlalchemy.orm import Session
from ..deps import db_session
from sqlalchemy import select

router = APIRouter(prefix="/agent/logs", tags=["agent"])

@router.get("/by-run/{run_id}")
def by_run(run_id: str, db: Session = Depends(db_session)) -> List[Dict[str, Any]]:
    rows = db.execute(select(AgentLog).where(AgentLog.run_id==run_id).order_by(AgentLog.created_at.asc())).scalars().all()
    return [{
        "id": str(r.id), "run_id": r.run_id, "thread_id": r.thread_id, "flow_id": r.flow_id,
        "step": r.step, "level": r.level, "message": r.message, "data": r.data, "created_at": r.created_at.isoformat()
    } for r in rows]

@router.get("/by-thread/{thread_id}")
def by_thread(thread_id: str, db: Session = Depends(db_session)) -> List[Dict[str, Any]]:
    rows = db.execute(select(AgentLog).where(AgentLog.thread_id==thread_id).order_by(AgentLog.created_at.asc())).scalars().all()
    return [{
        "id": str(r.id), "run_id": r.run_id, "thread_id": r.thread_id, "flow_id": r.flow_id,
        "step": r.step, "level": r.level, "message": r.message, "data": r.data, "created_at": r.created_at.isoformat()
    } for r in rows]