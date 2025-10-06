from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.flow_service import FlowService
from ..services.pipeline_service import PipelineService
from ..dto import CreateFlow, FlowOut, ThreadOut
from ..repositories.flow_summary_repo import get_active, active_payload
from typing import Any, Dict, List

router = APIRouter(prefix="/flows", tags=["flows"])

@router.get("", response_model=list[FlowOut])
def list_flows(db: Session = Depends(get_db)) -> List[FlowOut]:
    svc = FlowService(db)
    rows = svc.list()
    return [FlowOut(**row) for row in rows]

@router.post("", response_model=FlowOut, status_code=201)
def create_flow(payload: CreateFlow, db: Session = Depends(get_db)) -> FlowOut:
    svc = FlowService(db)
    return FlowOut(**svc.create(payload.slug, payload.name))

@router.get("/{flow_id}", response_model=FlowOut)
def get_flow(flow_id: str, db: Session = Depends(get_db)) -> FlowOut:
    svc = FlowService(db)
    row = svc.get_one(flow_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Flow not found")
    return FlowOut(**row)

@router.post("/{flow_id}/threads", response_model=ThreadOut, status_code=201)
def create_thread_for_flow(flow_id: str, db: Session = Depends(get_db)) -> ThreadOut:
    from ..services.thread_service import ThreadService
    return ThreadOut(**ThreadService(db).create(flow_id))

@router.get("/{flow_id}/pipelines")
def list_flow_pipelines(flow_id: str, published: int | None = None, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    return PipelineService(db).list_for_flow(flow_id, published=published)

@router.get("/{flow_id}/summary/active")
def get_active_flow_summary(flow_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    fs = get_active(db, flow_id)
    return active_payload(fs)

@router.delete("/{flow_id}", status_code=204)
def delete_flow(flow_id: str, db: Session = Depends(get_db)) -> Response:
    svc = FlowService(db)
    ok = svc.delete(flow_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Flow not found")
    # 204 No Content
    return Response(status_code=204)
