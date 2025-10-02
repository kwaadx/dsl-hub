from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Body, Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import SchemaChannel, SchemaDef

router = APIRouter(prefix="/schema", tags=["schema"]) 

@router.get("/channels")
def list_channels(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = db.execute(select(SchemaChannel)).scalars().all()
    out: List[Dict[str, Any]] = []
    for r in rows:
        sd = db.get(SchemaDef, r.active_schema_def_id)
        out.append({"name": r.name, "active_schema_def_id": str(r.active_schema_def_id), "def": {"id": str(sd.id), "name": sd.name, "version": sd.version}})
    return out

class ActivateChannelIn(BaseModel):
    schema_def_id: str

@router.post("/channels/{name}")
def activate_channel(name: str = Path(...), body: ActivateChannelIn = Body(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    ch = db.execute(select(SchemaChannel).where(SchemaChannel.name==name)).scalar_one_or_none()
    if not ch:
        # create channel if absent
        ch = SchemaChannel(name=name, active_schema_def_id=body.schema_def_id)
        db.add(ch)
        db.flush()
    else:
        ch.active_schema_def_id = body.schema_def_id
        db.flush()
    sd = db.get(SchemaDef, body.schema_def_id)
    return {"name": name, "active_schema_def_id": body.schema_def_id, "def": {"id": str(sd.id), "name": sd.name, "version": sd.version}}
