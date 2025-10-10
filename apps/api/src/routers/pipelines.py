from fastapi import APIRouter, Depends
from ..deps import uc_create_pipeline, uc_list_pipelines_for_flow
from sqlalchemy.orm import Session
from ..deps import db_session
from sqlalchemy.orm import Session
from ..services.pipeline_service import PipelineService
from ..dto import PublishAck
from typing import Any, Dict, List

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

@router.get("/by-flow/{flow_id}")
def list_pipelines(flow_id: str, published: int | None = None, db: Session = Depends(db_session)) -> List[Dict[str, Any]]:
    svc = PipelineService(db)
    return svc.list_for_flow(flow_id, published=published)

@router.get("/{pipeline_id}")
def get_pipeline(pipeline_id: str, db: Session = Depends(db_session)) -> Dict[str, Any]:
    svc = PipelineService(db)
    return svc.get(pipeline_id)

@router.post("/{pipeline_id}/publish", response_model=PublishAck)
def publish_pipeline(pipeline_id: str, db: Session = Depends(db_session)) -> PublishAck:
    svc = PipelineService(db)
    return PublishAck(**svc.publish(pipeline_id))
