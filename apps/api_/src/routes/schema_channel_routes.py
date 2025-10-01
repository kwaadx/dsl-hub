from fastapi import APIRouter, Depends, Path, Body, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..models.database import get_db
from ..controllers import schema_channel_controller as controller

router = APIRouter()

class SchemaChannelUpdate(BaseModel):
    active_schema_def_id: str

class SchemaChannelResponse(BaseModel):
    id: str
    name: str
    active_schema_def_id: str

    class Config:
        orm_mode = True

@router.get("/", response_model=List[SchemaChannelResponse])
async def list_channels(db: Session = Depends(get_db)):
    return controller.list_channels(db)

@router.put("/{name}", response_model=SchemaChannelResponse)
async def update_channel(name: str = Path(...), body: SchemaChannelUpdate = Body(...), db: Session = Depends(get_db)):
    return controller.set_active(db, name, body.active_schema_def_id)
