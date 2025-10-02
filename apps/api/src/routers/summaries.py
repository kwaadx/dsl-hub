from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..repositories.flow_summary_repo import get_active, active_payload
from ..repositories.thread_summary_repo import list_for_thread, payload as ts_payload

router = APIRouter(prefix="/summaries", tags=["summaries"])

@router.get("/flow/{flow_id}/active")
def get_flow_active(flow_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    fs = get_active(db, flow_id)
    return active_payload(fs)

@router.get("/thread/{thread_id}")
def list_thread_summaries(thread_id: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = list_for_thread(db, thread_id)
    return [ts_payload(r) for r in rows]
