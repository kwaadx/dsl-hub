from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List, Dict, Any
import uuid, json, hashlib, binascii
from ..models.models import Pipeline
from ..middleware.error import HTTPException

def list(
    db: Session,
    flow_id: Optional[str] = None,
    status: Optional[str] = None,
    is_published: Optional[bool] = None,
    schema_def_id: Optional[str] = None,
    version: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> List[Pipeline]:
    """
    List pipelines with optional filters and pagination.
    """
    q = db.query(Pipeline)
    if flow_id:
        q = q.filter(Pipeline.flow_id == flow_id)
    if status:
        q = q.filter(Pipeline.status == status)
    if is_published is not None:
        q = q.filter(Pipeline.is_published.is_(is_published))
    if schema_def_id:
        q = q.filter(Pipeline.schema_def_id == schema_def_id)
    if version:
        q = q.filter(Pipeline.version == version)
    q = q.order_by(Pipeline.created_at.desc())
    offset = (page - 1) * page_size
    return q.offset(offset).limit(page_size).all()

ALLOWED_STATUS = {"draft", "review", "published", "archived"}

def _sha256_json(obj: Dict[str, Any]) -> bytes:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).digest()

def create(db: Session, pipeline_data: Dict[str, Any]) -> Pipeline:
    """
    Create a new pipeline aligned with DB constraints.
    """
    # Generate a unique ID
    pipeline_id = str(uuid.uuid4())

    status = getattr(pipeline_data, "status", "draft") or "draft"
    if status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, message=f"Invalid status: {status}")

    is_published = bool(getattr(pipeline_data, "is_published", False))

    # Keep status/is_published coherent before hitting DB constraints
    if status == "published" and not is_published:
        # Auto-cohere to satisfy pipeline_status_published_ck
        is_published = True
    if is_published and status != "published":
        # User requests published flag but not published status
        raise HTTPException(status_code=400, message="is_published=true requires status='published'")

    # Optional external content hash as hex
    content_hash_hex = getattr(pipeline_data, "content_hash_hex", None)
    if content_hash_hex:
        try:
            content_hash = binascii.unhexlify(content_hash_hex)
        except binascii.Error:
            raise HTTPException(status_code=400, message="content_hash_hex must be a valid hex string")
        if len(content_hash) != 32:
            raise HTTPException(status_code=400, message="content_hash must be 32 bytes (SHA-256)")
    else:
        content_hash = _sha256_json(pipeline_data.content)

    # Enforce single published per flow (friendly check before DB unique-partial index)
    if is_published:
        exists = (
            db.query(Pipeline)
              .filter(and_(Pipeline.flow_id == pipeline_data.flow_id, Pipeline.is_published.is_(True)))
              .first()
        )
        if exists:
            raise HTTPException(status_code=409, message="Another published pipeline already exists for this flow")

    pipeline = Pipeline(
        id=pipeline_id,
        flow_id=pipeline_data.flow_id,
        version=pipeline_data.version,
        schema_def_id=pipeline_data.schema_def_id,
        status=status,
        is_published=is_published,
        content=pipeline_data.content,
        content_hash=content_hash,
        # schema_version: DB trigger sets via schema_def_id
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
