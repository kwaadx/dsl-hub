from fastapi import APIRouter, Depends, Query, Path, Body, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from ..models.database import get_db
from ..controllers import summary_controller as controller
from ..middleware.error import HTTPException

router = APIRouter()

# ---------- DTOs ----------
class FlowSummaryCreate(BaseModel):
    flow_id: str
    content: Dict[str, Any]
    pinned: Optional[Dict[str, Any]] = Field(default_factory=dict)
    last_message_id: Optional[str] = None
    is_active: Optional[bool] = False

class FlowSummaryResponse(BaseModel):
    id: str
    flow_id: str
    version: int
    content: Dict[str, Any]
    pinned: Dict[str, Any]
    last_message_id: Optional[str] = None
    is_active: bool

    class Config:
        orm_mode = True

class PagedFlowSummary(BaseModel):
    items: List[FlowSummaryResponse]
    page: int
    pageSize: int
    totalItems: int
    totalPages: int

class ThreadSummaryCreate(BaseModel):
    thread_id: str
    kind: Optional[str] = Field(default="short", description="short|detailed|system")
    content: Dict[str, Any]
    token_budget: Optional[int] = 1024
    covering_from: Optional[str] = None
    covering_to: Optional[str] = None

class ThreadSummaryResponse(BaseModel):
    id: str
    thread_id: str
    kind: str
    content: Dict[str, Any]
    token_budget: int

    class Config:
        orm_mode = True

class PagedThreadSummary(BaseModel):
    items: List[ThreadSummaryResponse]
    page: int
    pageSize: int
    totalItems: int
    totalPages: int

# ---------- Flow summaries ----------
@router.get("/flows", response_model=PagedFlowSummary)
async def list_flow_summaries(
    db: Session = Depends(get_db),
    flow_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    version: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=500),
):
    return controller.list_flow_summaries(db, flow_id, is_active, version, page, pageSize)

@router.post("/flows", response_model=FlowSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_flow_summary(body: FlowSummaryCreate = Body(...), db: Session = Depends(get_db)):
    return controller.create_flow_summary(db, body)

@router.post("/flows/{id}/activate", response_model=FlowSummaryResponse)
async def activate_flow_summary(id: str = Path(...), db: Session = Depends(get_db)):
    fs = controller.activate_flow_summary(db, id)
    if not fs:
        raise HTTPException(status_code=404, message="Flow summary not found")
    return fs

@router.get("/flows/{id}", response_model=FlowSummaryResponse)
async def get_flow_summary(id: str = Path(...), db: Session = Depends(get_db)):
    fs = controller.get_flow_summary(db, id)
    if not fs:
        raise HTTPException(status_code=404, message="Flow summary not found")
    return fs

# ---------- Thread summaries ----------
@router.get("/threads", response_model=PagedThreadSummary)
async def list_thread_summaries(
    db: Session = Depends(get_db),
    thread_id: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=500),
):
    return controller.list_thread_summaries(db, thread_id, kind, page, pageSize)

@router.post("/threads", response_model=ThreadSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_thread_summary(body: ThreadSummaryCreate = Body(...), db: Session = Depends(get_db)):
    return controller.create_thread_summary(db, body)

@router.get("/threads/{id}", response_model=ThreadSummaryResponse)
async def get_thread_summary(id: str = Path(...), db: Session = Depends(get_db)):
    ts = controller.get_thread_summary(db, id)
    if not ts:
        raise HTTPException(status_code=404, message="Thread summary not found")
    return ts
