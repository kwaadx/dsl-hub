from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..models import Flow, Pipeline

class FlowRepo:
    def __init__(self, db: Session):
        self.db = db

    def list(self):
        stmt = select(Flow)
        flows = self.db.execute(stmt).scalars().all()
        out = []
        for f in flows:
            has_pub = self.db.execute(
                select(func.count()).select_from(Pipeline).where(Pipeline.flow_id==f.id, Pipeline.is_published==True)
            ).scalar_one()
            active_ver = self.db.execute(
                select(Pipeline.version).where(Pipeline.flow_id==f.id, Pipeline.is_published==True).limit(1)
            ).scalar_one_or_none()
            out.append((f, bool(has_pub), active_ver))
        return out

    def create(self, flow_id, slug, name, meta=None):
        f = Flow(id=flow_id, slug=slug, name=name, meta=meta or {})
        self.db.add(f)
        self.db.flush()
        return f

    def get(self, flow_id):
        return self.db.get(Flow, flow_id)

    def delete(self, flow_id: str) -> bool:
        f = self.get(flow_id)
        if f is None:
            return False
        self.db.delete(f)
        # commit is handled by request lifecycle in get_db
        return True
