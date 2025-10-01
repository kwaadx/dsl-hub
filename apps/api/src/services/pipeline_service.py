import uuid, json, hashlib
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..repositories.pipeline_repo import PipelineRepo
from ..models import SchemaChannel, SchemaDef, Pipeline
from ..config import settings

class PipelineService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PipelineRepo(db)

    def list_for_flow(self, flow_id: str, published_only: bool=False):
        items = self.repo.list_for_flow(flow_id, published_only)
        return [{
            "id": str(p.id), "version": p.version, "status": p.status,
            "is_published": bool(p.is_published), "created_at": p.created_at.isoformat()
        } for p in items]

    def get(self, pid: str):
        p = self.repo.get(pid)
        return {
            "id": str(p.id), "flow_id": str(p.flow_id), "version": p.version,
            "status": p.status, "is_published": bool(p.is_published),
            "schema_version": p.schema_version, "schema_def_id": str(p.schema_def_id) if p.schema_def_id else None,
            "content": p.content
        }

    def _bump_patch(self, v: str | None) -> str:
        if not v:
            return "1.0.0"
        try:
            a,b,c = [int(x) for x in v.split(".")]
            return f"{a}.{b}.{c+1}"
        except Exception:
            return "1.0.1"

    def create_version(self, flow_id: str, content: dict, version: str | None = None):
        # pick active schema_def from channel
        channel = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.APP_SCHEMA_CHANNEL)).scalar_one_or_none()
        if not channel:
            raise ValueError("No schema channel configured")
        schema_def_id = channel.active_schema_def_id
        schema_ver = self.db.get(SchemaDef, schema_def_id).version
        # derive next version (patch) from latest for this flow
        last = self.db.query(Pipeline).filter(Pipeline.flow_id==flow_id).order_by(Pipeline.created_at.desc()).first()
        v = version or (self._bump_patch(last.version) if last else "1.0.0")
        pid = str(uuid.uuid4())
        canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        content_hash = hashlib.sha256(canonical).digest()
        p = self.repo.create_version(pid, flow_id, schema_def_id, v, content, status="draft", is_published=False, schema_version=schema_ver, content_hash=content_hash)
        return p

    def publish(self, pipeline_id: str):
        p = self.repo.publish(pipeline_id)
        return {"ok": True, "flow_id": str(p.flow_id), "version": p.version, "is_published": True}
