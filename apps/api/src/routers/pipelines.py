from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

@router.get("/by-flow/{flow_id}")
def list_pipelines(flow_id: str, published: int | None = None, db: Session = Depends(get_db)):
    svc = PipelineService(db)
    return svc.list_for_flow(flow_id, published_only=bool(published))

@router.get("/{pipeline_id}")
def get_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    svc = PipelineService(db)
    return svc.get(pipeline_id)

@router.post("/{pipeline_id}/publish")
def publish_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    svc = PipelineService(db)
    return svc.publish(pipeline_id)
