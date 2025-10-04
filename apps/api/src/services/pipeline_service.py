import uuid, json, hashlib
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..repositories.pipeline_repo import PipelineRepo
from ..models import SchemaChannel, SchemaDef, Pipeline
from ..config import settings

class PipelineService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PipelineRepo(db)

    def list_for_flow(self, flow_id: str, published: int | None = None) -> List[Dict[str, Any]]:
        # Interpret tri-state query param: None → all, 1 → only published, 0 → only unpublished
        pub_filter = True if published == 1 else False if published == 0 else None
        items = self.repo.list_for_flow(flow_id, pub_filter)
        return [{
            "id": str(p.id), "version": p.version, "status": p.status,
            "is_published": bool(p.is_published), "created_at": p.created_at.isoformat()
        } for p in items]

    def get(self, pid: str) -> Dict[str, Any]:
        p = self.repo.get(pid)
        return {
            "id": str(p.id), "flow_id": str(p.flow_id), "version": p.version,
            "status": p.status, "is_published": bool(p.is_published),
            "schema_version": p.schema_version, "schema_def_id": str(p.schema_def_id) if p.schema_def_id else None,
            "created_at": p.created_at.isoformat(),
            "content": p.content
        }

    @staticmethod
    def _bump_patch(v: str | None) -> str:
        if not v:
            return "1.0.0"
        try:
            a,b,c = [int(x) for x in v.split(".")]
            return f"{a}.{b}.{c+1}"
        except (ValueError, AttributeError):
            return "1.0.1"

    @staticmethod
    def _bump_major(v: str | None) -> str:
        if not v:
            return "1.0.0"
        try:
            a,b,c = [int(x) for x in v.split(".")]
            return f"{a+1}.0.0"
        except (ValueError, AttributeError):
            return "2.0.0"

    def create_version(self, flow_id: str, content: Dict[str, Any], version: str | None = None) -> Pipeline:
        # pick active schema_def from channel
        channel = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.SCHEMA_CHANNEL)).scalar_one_or_none()
        if not channel:
            raise ValueError("No schema channel configured")
        schema_def_id = channel.active_schema_def_id
        if not schema_def_id:
            raise ValueError("No active schema definition in the configured channel")
        schema_ver = self.db.get(SchemaDef, schema_def_id).version
        # derive next version: bump major if schema_def changed since last, else patch
        last = self.db.query(Pipeline).filter(Pipeline.flow_id==flow_id).order_by(Pipeline.created_at.desc()).first()
        if version:
            v = version
        else:
            if last and str(getattr(last, "schema_def_id", None)) != str(schema_def_id):
                v = self._bump_major(getattr(last, "version", None))
            else:
                v = self._bump_patch(getattr(last, "version", None) if last else None)
        pid = str(uuid.uuid4())
        canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        content_hash = hashlib.sha256(canonical).digest()
        p = self.repo.create_version(pipeline_id=pid, flow_id=flow_id, schema_def_id=schema_def_id, version=v, content=content, status="draft", is_published=False, schema_version=schema_ver, content_hash=content_hash)
        return p

    def publish(self, pipeline_id: str) -> Dict[str, Any]:
        # Perform publish under transaction (handled by get_db). Repo locks rows to avoid races.
        p = self.repo.publish(pipeline_id)
        # Conflict detection: ensure exactly one published for the flow
        from sqlalchemy import select, func
        from fastapi import HTTPException
        cnt = self.db.execute(
            select(func.count()).select_from(Pipeline).where(Pipeline.flow_id == p.flow_id, Pipeline.is_published == True)
        ).scalar_one()
        if cnt and int(cnt) > 1:
            # Let the middleware rollback the transaction
            raise HTTPException(status_code=409, detail="Publish conflict: multiple published versions for this flow")
        return {"ok": True, "flow_id": str(p.flow_id), "version": p.version, "is_published": True}
