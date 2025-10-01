from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.models import SchemaChannel, SchemaDef
from ..middleware.error import HTTPException


def list_channels(db: Session) -> List[SchemaChannel]:
    return db.query(SchemaChannel).order_by(SchemaChannel.name.asc()).all()


def get_by_name(db: Session, name: str) -> Optional[SchemaChannel]:
    return db.query(SchemaChannel).filter(SchemaChannel.name == name).first()


def set_active(db: Session, name: str, active_schema_def_id: str) -> SchemaChannel:
    # Validate schema_def exists
    schema = db.query(SchemaDef).filter(SchemaDef.id == active_schema_def_id).first()
    if not schema:
        raise HTTPException(status_code=400, message="schema_def not found")

    ch = get_by_name(db, name)
    if ch is None:
        # Create
        ch = SchemaChannel(name=name, active_schema_def_id=active_schema_def_id)
        db.add(ch)
    else:
        # Update
        ch.active_schema_def_id = active_schema_def_id

    db.commit()
    db.refresh(ch)
    return ch
