from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models import Pipeline

class PipelineRepo:
    def __init__(self, db: Session):
        self.db = db

    def list_for_flow(self, flow_id, published_only=False):
        q = self.db.query(Pipeline).filter(Pipeline.flow_id==flow_id)
        if published_only:
            q = q.filter(Pipeline.is_published==True)
        return q.order_by(Pipeline.created_at.desc()).all()

    def get(self, pid):
        return self.db.get(Pipeline, pid)

    def create_version(self, id, flow_id, schema_def_id, version, content, status="draft", is_published=False, schema_version=None, content_hash=None):
        p = Pipeline(
            id=id,
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

    def publish(self, pid):
        p = self.get(pid)
        # unpublish others
        self.db.query(Pipeline).filter(Pipeline.flow_id==p.flow_id, Pipeline.id!=pid, Pipeline.is_published==True).update({"is_published": False, "status":"draft"})
        p.is_published = True
        p.status = "published"
        self.db.flush()
        return p
