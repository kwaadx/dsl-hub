from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import uuid
from ..models.models import Pipeline
from ..middleware.error import HTTPException

def list(db: Session) -> List[Pipeline]:
    """
    List all pipelines.
    """
    return db.query(Pipeline).all()

def create(db: Session, pipeline_data: Dict[str, Any]) -> Pipeline:
    """
    Create a new pipeline.
    """
    # Generate a unique ID
    pipeline_id = str(uuid.uuid4())

    # Create pipeline
    pipeline = Pipeline(
        id=pipeline_id,
        flow_id=pipeline_data.flow_id,
        version=pipeline_data.version,
        schema_version=pipeline_data.schema_version,
        content=pipeline_data.content
    )

    # Save to database
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    return pipeline

def get(db: Session, pipeline_id: str) -> Optional[Pipeline]:
    """
    Get a pipeline by ID.
    """
    return db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

def remove(db: Session, pipeline_id: str) -> bool:
    """
    Remove a pipeline by ID.
    """
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        return False

    db.delete(pipeline)
    db.commit()

    return True
