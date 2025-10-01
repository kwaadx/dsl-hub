from fastapi import APIRouter, Depends, Path, Body, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from ..models.database import get_db
from ..controllers import flow_controller

router = APIRouter()

class FlowCreate(BaseModel):
    name: Optional[str] = None

class FlowResponse(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True

@router.get("/", response_model=List[FlowResponse])
async def list_flows(db: Session = Depends(get_db)):
    """
    List all flows.
    """
    return flow_controller.list(db)

@router.post("/", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(flow: FlowCreate = Body(...), db: Session = Depends(get_db)):
    """
    Create a new flow.
    """
    return flow_controller.create(db, flow)

@router.get("/{id}", response_model=FlowResponse)
async def get_flow(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Get a flow by ID.
    """
    flow = flow_controller.get(db, id)
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    return flow

@router.delete("/{id}")
async def delete_flow(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Delete a flow by ID.
    """
    ok = flow_controller.remove(db, id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    return {"ok": True}

@router.post("/{id}/threads/new-or-active")
async def new_or_active_thread(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Create a new thread or get an active thread for a flow.
    """
    return flow_controller.new_or_active_thread(db, id)
