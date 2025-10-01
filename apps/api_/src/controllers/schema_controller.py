from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import uuid
from ..models.models import SchemaDef
from ..middleware.error import HTTPException

def list(db: Session, name: Optional[str] = None, version: Optional[str] = None, status: Optional[str] = None, page: int = 1, page_size: int = 100) -> List[SchemaDef]:
    """
    List schemas with optional filters and pagination.
    """
    q = db.query(SchemaDef)
    if name:
        q = q.filter(SchemaDef.name == name)
    if version:
        q = q.filter(SchemaDef.version == version)
    if status:
        q = q.filter(SchemaDef.status == status)
    q = q.order_by(SchemaDef.created_at.desc())
    offset = (page - 1) * page_size
    return q.offset(offset).limit(page_size).all()

def create(db: Session, schema_data: Dict[str, Any]) -> SchemaDef:
    """
    Create a new schema.
    """
    # Generate a unique ID
    schema_id = str(uuid.uuid4())

    # Create schema
    schema = SchemaDef(
        id=schema_id,
        name=schema_data.name,
        version=schema_data.version,
        json=schema_data.json
    )

    # Save to database
    db.add(schema)
    db.commit()
    db.refresh(schema)

    return schema

def get(db: Session, schema_id: str) -> Optional[SchemaDef]:
    """
    Get a schema by ID.
    """
    return db.query(SchemaDef).filter(SchemaDef.id == schema_id).first()

def remove(db: Session, schema_id: str) -> bool:
    """
    Remove a schema by ID.
    """
    schema = db.query(SchemaDef).filter(SchemaDef.id == schema_id).first()
    if not schema:
        return False

    db.delete(schema)
    db.commit()

    return True
