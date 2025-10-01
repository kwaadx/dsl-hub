from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import SchemaChannel, SchemaDef

router = APIRouter(prefix="/schema", tags=["schema"])

@router.get("/channels")
def list_channels(db: Session = Depends(get_db)):
    rows = db.execute(select(SchemaChannel)).scalars().all()
    out = []
    for r in rows:
        sd = db.get(SchemaDef, r.active_schema_def_id)
        out.append({"name": r.name, "active_schema_def_id": str(r.active_schema_def_id), "def": {"id": str(sd.id), "name": sd.name, "version": sd.version}})
    return out
