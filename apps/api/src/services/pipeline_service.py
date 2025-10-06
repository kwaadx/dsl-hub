import hashlib
import json
import uuid
from typing import Any, Dict, List

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..config import settings
from ..middleware.error import AppError
from ..models import Flow, Pipeline, SchemaChannel, SchemaDef
from ..repositories.pipeline_repo import PipelineRepo

class PipelineService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PipelineRepo(db)

    def _require_flow(self, flow_id: str) -> None:
        if self.db.get(Flow, flow_id) is None:
            raise AppError(status=404, code="FLOW_NOT_FOUND", message="Flow not found")

    def list_for_flow(self, flow_id: str, published: int | None = None) -> List[Dict[str, Any]]:
        # Interpret tri-state query param: None → all, 1 → only published, 0 → only unpublished
        pub_filter = True if published == 1 else False if published == 0 else None
        self._require_flow(flow_id)
        items = self.repo.list_for_flow(flow_id, pub_filter)
        return [{
            "id": str(p.id), "version": p.version, "status": p.status,
            "is_published": bool(p.is_published), "created_at": p.created_at.isoformat()
        } for p in items]

    def get(self, pid: str) -> Dict[str, Any]:
        p = self.repo.get(pid)
        if p is None:
            raise AppError(status=404, code="PIPELINE_NOT_FOUND", message="Pipeline not found")
        return dict(
            id=str(p.id), flow_id=str(p.flow_id), version=p.version,
            status=p.status, is_published=bool(p.is_published),
            schema_version=p.schema_version, schema_def_id=str(p.schema_def_id) if p.schema_def_id else None,
            created_at=p.created_at.isoformat(),
            content=p.content
        )

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
        self._require_flow(flow_id)
        channel = self.db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.SCHEMA_CHANNEL)).scalar_one_or_none()
        if not channel:
            raise AppError(status=503, code="SCHEMA_CHANNEL_MISSING", message="No schema channel configured")
        schema_def_id = channel.active_schema_def_id
        if not schema_def_id:
            raise AppError(status=503, code="SCHEMA_DEFINITION_MISSING",
                           message="No active schema definition in the configured channel")
        schema_def = self.db.get(SchemaDef, schema_def_id)
        if schema_def is None:
            raise AppError(status=503, code="SCHEMA_DEFINITION_MISSING",
                           message="Active schema definition is not available")
        schema_ver = schema_def.version
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
        p = self.repo.publish(pipeline_id)
        if p is None:
            raise AppError(status=404, code="PIPELINE_NOT_FOUND", message="Pipeline not found")
        # Conflict detection: ensure exactly one published for the flow
        cnt = self.db.execute(
            select(func.count()).select_from(Pipeline).where(Pipeline.flow_id == p.flow_id, Pipeline.is_published == True)
        ).scalar_one()
        if cnt and int(cnt) > 1:
            raise AppError(status=409, code="PIPELINE_PUBLISH_CONFLICT",
                           message="Publish conflict: multiple published versions for this flow")
        return dict(ok=True, flow_id=str(p.flow_id), version=p.version, is_published=True)
