import uuid
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from ..middleware.error import AppError
from ..repositories.flow_repo import FlowRepo
from ..models import Flow

class FlowService:
    def __init__(self, db: Session):
        self.repo = FlowRepo(db)

    def list(self) -> List[Dict[str, Any]]:
        rows = self.repo.list()
        out: List[Dict[str, Any]] = []
        for flow, pub_count, active_ver in rows:
            out.append(self._serialize(flow, int(pub_count or 0), active_ver))
        return out

    def get_one(self, flow_id: str) -> Dict[str, Any]:
        row = self.repo.get_with_stats(flow_id)
        if row is None:
            raise AppError(status=404, code="FLOW_NOT_FOUND", message="Flow not found")
        flow, pub_count, active_ver = row
        return self._serialize(flow, int(pub_count or 0), active_ver)

    def create(self, slug: str, name: str) -> Dict[str, Any]:
        fid = str(uuid.uuid4())
        f = self.repo.create(fid, slug, name, meta={})
        return self._serialize(f, 0, None)

    def update(self, flow_id: str, *, name: str | None = None, slug: str | None = None) -> Dict[str, Any]:
        if name is None and slug is None:
            raise AppError(status=400, code="FLOW_NOTHING_TO_UPDATE", message="Provide name or slug to update")
        f = self.repo.update(flow_id, name=name, slug=slug)
        if f is None:
            raise AppError(status=404, code="FLOW_NOT_FOUND", message="Flow not found")
        # Flush above ensures DB state is current; fetch aggregated stats for response
        return self.get_one(flow_id)

    def delete(self, flow_id: str) -> None:
        deleted = self.repo.delete(flow_id)
        if not deleted:
            raise AppError(status=404, code="FLOW_NOT_FOUND", message="Flow not found")

    def _serialize(self, flow: Flow, published_count: int, active_version: Any) -> Dict[str, Any]:
        version = str(active_version) if active_version else None
        return {
            "id": str(flow.id),
            "slug": flow.slug,
            "name": flow.name,
            "has_published": published_count > 0,
            "active_version": version,
        }
