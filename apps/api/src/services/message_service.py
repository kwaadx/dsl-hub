import uuid
from sqlalchemy.orm import Session
from ..repositories.message_repo import MessageRepo

class MessageService:
    def __init__(self, db: Session):
        self.repo = MessageRepo(db)

    def add(self, thread_id: str, role: str, content, parent_id=None, tool_name=None, tool_result=None, format="text"):
        mid = str(uuid.uuid4())
        m = self.repo.add(mid, thread_id, role, content, parent_id, tool_name, tool_result, format)
        return {"id": str(m.id), "created_at": m.created_at.isoformat()}

    def list(self, thread_id: str, limit: int = 50):
        return [{
            "id": str(m.id), "role": m.role, "format": m.format, "content": m.content,
            "created_at": m.created_at.isoformat(), "parent_id": str(m.parent_id) if m.parent_id else None
        } for m in self.repo.list_for_thread(thread_id, limit=limit)]
