from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.flow_service import FlowService
from ..services.pipeline_service import PipelineService
from ..dto import CreateFlow, FlowOut, ThreadOut
from ..repositories.flow_summary_repo import get_active, active_payload

router = APIRouter(prefix="/flows", tags=["flows"])

@router.get("", response_model=list[FlowOut])
def list_flows(db: Session = Depends(get_db)):
    svc = FlowService(db)
    return svc.list()

@router.post("", response_model=FlowOut, status_code=201)
def create_flow(payload: CreateFlow, db: Session = Depends(get_db)):
    svc = FlowService(db)
    return svc.create(payload.slug, payload.name)

@router.post("/{flow_id}/threads", response_model=ThreadOut, status_code=201)
def create_thread_for_flow(flow_id: str, db: Session = Depends(get_db)):
    from ..services.thread_service import ThreadService
    return ThreadService(db).create(flow_id)

@router.get("/{flow_id}/pipelines")
def list_flow_pipelines(flow_id: str, published: int | None = None, db: Session = Depends(get_db)):
    return PipelineService(db).list_for_flow(flow_id, published=published)

@router.get("/{flow_id}/summary/active")
def get_active_flow_summary(flow_id: str, db: Session = Depends(get_db)):
    fs = get_active(db, flow_id)
    return active_payload(fs)
