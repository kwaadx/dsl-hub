import uuid
from sqlalchemy.orm import Session
from ..repositories.thread_repo import ThreadRepo

class ThreadService:
    def __init__(self, db: Session):
        self.repo = ThreadRepo(db)

    def create(self, flow_id: str):
        tid = str(uuid.uuid4())
        t = self.repo.create(tid, flow_id)
        return dict(id=str(t.id), flow_id=str(t.flow_id), status=t.status, started_at=t.started_at.isoformat())
