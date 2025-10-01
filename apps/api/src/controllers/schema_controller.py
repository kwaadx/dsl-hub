from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import uuid
from ..models.models import SchemaDef
from ..middleware.error import HTTPException

def list(db: Session) -> List[SchemaDef]:
    """
    List all schemas.
    """
    return db.query(SchemaDef).all()

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
