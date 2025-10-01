from fastapi import APIRouter, Depends, Path, status, Body, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..models.database import get_db
from ..controllers import thread_controller
from ..middleware.error import HTTPException

router = APIRouter()

class ThreadResponse(BaseModel):
    id: str
    flow_id: str
    status: str
    archived: bool

    class Config:
        orm_mode = True

@router.get("/", response_model=List[ThreadResponse])
async def list_threads(
    db: Session = Depends(get_db),
    flow_id: Optional[str] = None,
    status: Optional[str] = None,
    archived: Optional[bool] = None,
    page: int = 1,
    pageSize: int = 100,
):
    """
    List threads with optional filters and pagination (returns page items only).
    """
    return thread_controller.list(db, flow_id=flow_id, status=status, archived=archived, page=page, page_size=pageSize)

@router.get("/{id}", response_model=ThreadResponse)
async def get_thread(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Get a thread by ID.
    """
    thread = thread_controller.get(db, id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Thread not found")
    return thread

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Delete a thread by ID.
    """
    ok = thread_controller.remove(db, id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Thread not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/{id}/archive")
async def archive_thread(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Archive a thread.
    """
    thread = thread_controller.archive(db, id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, message="Thread not found")
    return thread

# ======================
# Messages API
# ======================
ALLOWED_ROLES = {"user", "assistant", "system", "tool"}
ALLOWED_FORMATS = {"text", "markdown", "json", "buttons", "card"}

class MessageCreate(BaseModel):
    role: str = Field(..., description="user|assistant|system|tool")
    format: str = Field("text", description="text|markdown|json|buttons|card")
    content: Dict[str, Any] | List[Dict[str, Any]]
    parent_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    id: str
    thread_id: str
    role: str
    format: str
    content: Dict[str, Any]

    class Config:
        orm_mode = True

@router.get("/{id}/messages", response_model=List[MessageResponse])
async def list_messages(id: str = Path(...), db: Session = Depends(get_db)):
    return thread_controller.list_messages(db, id)

@router.post("/{id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(id: str = Path(...), msg: MessageCreate = Body(...), db: Session = Depends(get_db)):
    return thread_controller.create_message(db, id, msg)
