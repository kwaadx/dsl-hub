from fastapi import APIRouter, Depends, Path, Body, status, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..models.database import get_db
from ..controllers import pipeline_controller
from ..middleware.error import HTTPException

router = APIRouter()

class PipelineCreate(BaseModel):
    flow_id: str
    version: str = Field(..., regex=r"^\d+\.\d+\.\d+$", description="semver X.Y.Z")
    schema_def_id: str  # reference to schema_def
    content: Dict[str, Any]
    status: Optional[str] = Field(default="draft")            # draft|review|published|archived
    is_published: Optional[bool] = Field(default=False)
    content_hash_hex: Optional[str] = None  # optional hex SHA-256

class PipelineResponse(BaseModel):
    id: str
    flow_id: str
    version: str
    schema_version: str
    status: str
    is_published: bool
    content: Dict[str, Any]

    class Config:
        orm_mode = True

@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    db: Session = Depends(get_db),
    flow_id: Optional[str] = None,
    status: Optional[str] = None,
    is_published: Optional[bool] = None,
    schema_def_id: Optional[str] = None,
    version: Optional[str] = None,
    page: int = 1,
    pageSize: int = 100,
):
    """
    List pipelines with optional filters and pagination (returns page items only).
    """
    return pipeline_controller.list(
        db,
        flow_id=flow_id,
        status=status,
        is_published=is_published,
        schema_def_id=schema_def_id,
        version=version,
        page=page,
        page_size=pageSize,
    )

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Pipeline not found")
    return pipeline

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Delete a pipeline by ID.
    """
    ok = pipeline_controller.remove(db, id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Pipeline not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
