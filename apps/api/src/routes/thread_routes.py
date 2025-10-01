from fastapi import APIRouter, Depends, Path, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from ..models.database import get_db
from ..controllers import thread_controller

router = APIRouter()

class ThreadResponse(BaseModel):
    id: str
    flow_id: str
    status: str
    archived: bool

    class Config:
        orm_mode = True

@router.get("/", response_model=List[ThreadResponse])
async def list_threads(db: Session = Depends(get_db)):
    """
    List all threads.
    """
    return thread_controller.list(db)

@router.get("/{id}", response_model=ThreadResponse)
async def get_thread(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Get a thread by ID.
    """
    thread = thread_controller.get(db, id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return thread

@router.delete("/{id}")
async def delete_thread(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Delete a thread by ID.
    """
    ok = thread_controller.remove(db, id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return {"ok": True}

@router.post("/{id}/archive")
async def archive_thread(id: str = Path(...), db: Session = Depends(get_db)):
    """
    Archive a thread.
    """
    thread = thread_controller.archive(db, id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return thread
