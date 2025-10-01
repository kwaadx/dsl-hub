from fastapi import APIRouter, Depends, Path, Body, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from ..models.database import get_db
from ..controllers import pipeline_controller

router = APIRouter()

class PipelineCreate(BaseModel):
    flow_id: str
    version: str
    schema_version: str
    content: Dict[str, Any]

class PipelineResponse(BaseModel):
    id: str
    flow_id: str
    version: str
    schema_version: str
    status: str
    content: Dict[str, Any]

    class Config:
        orm_mode = True

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(db: Session = Depends(get_db)):
    """
    List all pipelines.
    """
    return pipeline_controller.list(db)

@router.post("/", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(pipeline: PipelineCreate = Body(...), db: Session = Depends(get_db)):
    """
    Create a new pipeline.
    """
    return pipeline_controller.create(db, pipeline)

@router.get("/{id}", response_model=PipelineResponse)
async def get_pipeline(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Get a pipeline by ID.
    """
    pipeline = pipeline_controller.get(db, id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline

@router.delete("/{id}")
async def delete_pipeline(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Delete a pipeline by ID.
    """
    ok = pipeline_controller.remove(db, id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return {"ok": True}
