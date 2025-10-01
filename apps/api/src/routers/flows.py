from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.flow_service import FlowService
from ..dto import CreateFlow, FlowOut

router = APIRouter(prefix="/flows", tags=["flows"])

@router.get("", response_model=list[FlowOut])
def list_flows(db: Session = Depends(get_db)):
    svc = FlowService(db)
    return svc.list()

@router.post("", response_model=FlowOut, status_code=201)
def create_flow(payload: CreateFlow, db: Session = Depends(get_db)):
    svc = FlowService(db)
    return svc.create(payload.slug, payload.name)
