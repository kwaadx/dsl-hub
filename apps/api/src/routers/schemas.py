from typing import List
from fastapi import APIRouter, Depends, Body, Path, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import SchemaChannel, SchemaDef
from ..dto import SchemaChannelOut, SchemaDefBrief

router = APIRouter(prefix="/schema", tags=["schema"]) 

@router.get("/channels", response_model=List[SchemaChannelOut])
def list_channels(db: Session = Depends(get_db)) -> List[SchemaChannelOut]:
    rows = db.execute(select(SchemaChannel)).scalars().all()
    out: List[SchemaChannelOut] = []
    for r in rows:
        sd = db.get(SchemaDef, r.active_schema_def_id)
        if not sd:
            # Guard against dangling FK; return minimal data
            out.append(SchemaChannelOut(**dict(name=r.name, active_schema_def_id=str(r.active_schema_def_id), def_=None)))
        else:
            brief = SchemaDefBrief(id=str(sd.id), name=sd.name, version=sd.version)
            out.append(SchemaChannelOut(**dict(name=r.name, active_schema_def_id=str(r.active_schema_def_id), def_=brief)))
    return out

class ActivateChannelIn(BaseModel):
    schema_def_id: str

@router.post("/channels/{name}", response_model=SchemaChannelOut)
def activate_channel(name: str = Path(...), body: ActivateChannelIn = Body(...), db: Session = Depends(get_db)) -> SchemaChannelOut:
    # Validate target schema_def exists before changing channel
    sd = db.get(SchemaDef, body.schema_def_id)
    if not sd:
        raise HTTPException(status_code=400, detail="Invalid schema_def_id")
    ch = db.execute(select(SchemaChannel).where(SchemaChannel.name==name)).scalar_one_or_none()
    if not ch:
        # create channel if absent
        ch = SchemaChannel(name=name, active_schema_def_id=body.schema_def_id)
        db.add(ch)
    else:
        ch.active_schema_def_id = body.schema_def_id
    db.flush()
    brief = SchemaDefBrief(id=str(sd.id), name=sd.name, version=sd.version)
    return SchemaChannelOut(**dict(name=name, active_schema_def_id=body.schema_def_id, def_=brief))
