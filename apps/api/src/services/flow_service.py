import uuid
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from ..repositories.flow_repo import FlowRepo

class FlowService:
    def __init__(self, db: Session):
        self.repo = FlowRepo(db)

    def list(self) -> List[Dict[str, Any]]:
        rows = self.repo.list()
        out: List[Dict[str, Any]] = []
        for f, has_pub, ver in rows:
            out.append({
                "id": str(f.id), "slug": f.slug, "name": f.name,
                "has_published": has_pub, "active_version": ver
            })
        return out

    def get_one(self, flow_id: str) -> Dict[str, Any] | None:
        f = self.repo.get(flow_id)
        if f is None:
            return None
        return dict(id=str(f.id), slug=f.slug, name=f.name)

    def create(self, slug: str, name: str) -> Dict[str, Any]:
        fid = str(uuid.uuid4())
        f = self.repo.create(fid, slug, name, meta={})
        return dict(id=str(f.id), slug=f.slug, name=f.name)

    def delete(self, flow_id: str) -> bool:
        return self.repo.delete(flow_id)
