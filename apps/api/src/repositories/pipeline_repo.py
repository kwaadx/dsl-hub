from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Pipeline

class PipelineRepo:
    def __init__(self, db: Session):
        self.db = db

    def list_for_flow(self, flow_id: str, published_only: bool = False) -> List[Pipeline]:
        stmt = select(Pipeline).where(Pipeline.flow_id == flow_id)
        if published_only:
            stmt = stmt.where(Pipeline.is_published == True)
        stmt = stmt.order_by(Pipeline.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get(self, pid: str) -> Pipeline:
        return self.db.get(Pipeline, pid)

    def create_version(
        self,
        pipeline_id: str,
        flow_id: str,
        schema_def_id: str,
        version: str,
        content: Dict[str, Any],
        status: str = "draft",
        is_published: bool = False,
        schema_version: Optional[str] = None,
        content_hash: Optional[bytes] = None,
    ) -> Pipeline:
        p = Pipeline(
            id=pipeline_id,
            flow_id=flow_id,
            schema_def_id=schema_def_id,
            version=version,
            content=content,
            status=status,
            is_published=is_published,
            schema_version=schema_version or "1.0.0",
            content_hash=content_hash,
        )
        self.db.add(p); self.db.flush()
        return p

    def publish(self, pid: str) -> Pipeline:
        p = self.get(pid)
        # unpublish others
        self.db.query(Pipeline).filter(Pipeline.flow_id==p.flow_id, Pipeline.id!=pid, Pipeline.is_published==True).update({"is_published": False, "status":"draft"})
        p.is_published = True
        p.status = "published"
        self.db.flush()
        return p
