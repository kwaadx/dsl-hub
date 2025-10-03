from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Pipeline

class PipelineRepo:
    def __init__(self, db: Session):
        self.db = db

    def list_for_flow(self, flow_id: str, published: Optional[bool] = None) -> List[Pipeline]:
        stmt = select(Pipeline).where(Pipeline.flow_id == flow_id)
        if published is True:
            stmt = stmt.where(Pipeline.is_published == True)
        elif published is False:
            stmt = stmt.where(Pipeline.is_published == False)
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
        # Lock all pipelines of the same flow to avoid concurrent publish races
        _ = (
            self.db.query(Pipeline)
            .filter(Pipeline.flow_id == p.flow_id)
            .with_for_update()
            .all()
        )
        # unpublish others
        self.db.query(Pipeline).filter(
            Pipeline.flow_id == p.flow_id,
            Pipeline.id != pid,
            Pipeline.is_published == True,
        ).update({"is_published": False, "status": "draft"})
        p.is_published = True
        p.status = "published"
        self.db.flush()
        return p
