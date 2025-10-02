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

    def create(self, slug: str, name: str) -> Dict[str, Any]:
        fid = str(uuid.uuid4())
        f = self.repo.create(fid, slug, name, meta={})
        return {"id": str(f.id), "slug": f.slug, "name": f.name}
