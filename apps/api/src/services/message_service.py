import uuid
from sqlalchemy.orm import Session
from ..repositories.message_repo import MessageRepo

ALLOWED_ROLES = {"user", "assistant", "system", "tool"}
ALLOWED_FORMATS = {"text", "markdown", "json", "buttons", "card"}

class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MessageRepo(db)

    def add(self, thread_id: str, role: str, content, parent_id=None, tool_name=None, tool_result=None, format="text"):
        if role not in ALLOWED_ROLES:
            raise ValueError("Invalid role")
        if format not in ALLOWED_FORMATS:
            raise ValueError("Invalid format")
        if role == "tool" and not tool_name:
            raise ValueError("tool_name required for role=tool")
        # parent must belong to the same thread
        if parent_id:
            from ..models import Message
            parent = self.db.get(Message, parent_id)
            if not parent or str(parent.thread_id) != thread_id:
                raise ValueError("parent_id must belong to the same thread")
        mid = str(uuid.uuid4())
        m = self.repo.add(mid, thread_id, role, content, parent_id, tool_name, tool_result, format)
        return {"id": str(m.id), "created_at": m.created_at.isoformat()}

    def list(self, thread_id: str, limit: int = 50, before: str | None = None):
        from datetime import datetime
        from ..models import Message
        q = self.db.query(Message).filter(Message.thread_id == thread_id)
        if before:
            ts = before
            if isinstance(ts, str) and ts.endswith("Z"):
                ts = ts.replace("Z", "+00:00")
            q = q.filter(Message.created_at < datetime.fromisoformat(ts))
        q = q.order_by(Message.created_at.desc()).limit(limit)
        rows = q.all()
        return [{
            "id": str(m.id), "role": m.role, "format": m.format, "content": m.content,
            "created_at": m.created_at.isoformat(), "parent_id": str(m.parent_id) if m.parent_id else None
        } for m in rows]
