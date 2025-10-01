from fastapi import APIRouter, Depends, Path, Body, status, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ..models.database import get_db
from ..controllers import flow_controller
from ..middleware.error import HTTPException

router = APIRouter()

class FlowCreate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None

class FlowUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None

class FlowResponse(BaseModel):
    id: str
    name: str
    slug: str

    class Config:
        orm_mode = True

@router.get("/", response_model=List[FlowResponse])
async def list_flows(q: Optional[str] = Query(None), page: int = Query(1, ge=1), pageSize: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    """
    List flows with optional search and pagination. Returns current page items only.
    """
    return flow_controller.list(db, q=q, page=page, page_size=pageSize)

@router.post("/", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(flow: FlowCreate = Body(...), db: Session = Depends(get_db)):
    """
    Create a new flow.
    """
    return flow_controller.create(db, flow)

@router.patch("/{id}", response_model=FlowResponse)
async def patch_flow(id: str = Path(...), patch: FlowUpdate = Body(...), db: Session = Depends(get_db)):
    flow = flow_controller.update(db, id, patch)
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Flow not found")
    return flow

@router.get("/{id}", response_model=FlowResponse)
async def get_flow(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Get a flow by ID.
    """
    flow = flow_controller.get(db, id)
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Flow not found")
    return flow

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Delete a flow by ID.
    """
    ok = flow_controller.remove(db, id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Flow not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{id}/threads/new-or-active")
async def new_or_active_thread(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Create a new thread or get an active thread for a flow.
    """
    return flow_controller.new_or_active_thread(db, id)
