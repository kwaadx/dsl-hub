from pydantic import BaseModel, Field
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from ..deps import uc_list_thread_summaries
from sqlalchemy.orm import Session
from ..deps import db_session
from ..repositories.flow_summary_repo import get_active, active_payload
from ..repositories.thread_summary_repo import list_for_thread, payload as ts_payload

router = APIRouter(prefix="/summaries", tags=["summaries"])

@router.get("/flow/{flow_id}/active")
def get_flow_active(flow_id: str, db: Session = Depends(db_session)) -> Dict[str, Any]:
    fs = get_active(db, flow_id)
    return active_payload(fs)

@router.get("/thread/{thread_id}")
def list_thread_summaries(thread_id: str, uc = Depends(uc_list_thread_summaries)) -> List[Dict[str, Any]]:
    return uc(thread_id=thread_id)


class GenerateThreadSummaryIn(BaseModel):
    kind: str = Field(default="short", pattern=r"^(short|long)$")

@router.post("/thread/{thread_id}/generate")
async def generate_thread_summary(thread_id: str, body: GenerateThreadSummaryIn, uc = Depends(uc_generate_thread_summary)) -> Dict[str, Any]:
    return await uc(thread_id=thread_id, kind=body.kind)

class RefreshFlowSummaryIn(BaseModel):
    thread_ids: List[str] | None = None

@router.post("/flow/{flow_id}/refresh")
async def refresh_flow_summary(flow_id: str, body: RefreshFlowSummaryIn, uc = Depends(uc_refresh_flow_summary)) -> Dict[str, Any]:
    return await uc(flow_id=flow_id, thread_ids=body.thread_ids)
