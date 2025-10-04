import uuid
from typing import Any, Optional, List, Dict
from sqlalchemy.orm import Session
from ..repositories.message_repo import MessageRepo
from ..middleware.error import AppError

ALLOWED_ROLES = {"user", "assistant", "system", "tool"}
ALLOWED_FORMATS = {"text", "markdown", "json", "buttons", "card"}

class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MessageRepo(db)

    def add(
        self,
        thread_id: str,
        role: str,
        content: Any,
        parent_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_result: Optional[Any] = None,
        fmt: str = "text",
    ) -> Dict[str, str]:
        if role not in ALLOWED_ROLES:
            raise AppError(status=400, code="BAD_ROLE", message=f"Invalid role: {role}")
        if fmt not in ALLOWED_FORMATS:
            raise AppError(status=400, code="BAD_FORMAT", message=f"Invalid format: {fmt}")
        if role == "tool" and not tool_name:
            raise AppError(status=400, code="TOOL_NAME_REQUIRED", message="tool_name required for role=tool")
        # parent must belong to the same thread
        if parent_id:
            from ..models import Message
            parent = self.db.get(Message, parent_id)
            if not parent or str(parent.thread_id) != thread_id:
                raise AppError(status=400, code="PARENT_NOT_SAME_THREAD", message="parent_id must belong to the same thread")
        mid = str(uuid.uuid4())
        m = self.repo.add(mid, thread_id, role, content, parent_id, tool_name, tool_result, fmt)
        return dict(id=str(m.id), created_at=m.created_at.isoformat())

    def list(self, thread_id: str, limit: int = 50, before: Optional[str] = None) -> List[Dict[str, Any]]:
        from datetime import datetime
        from ..models import Message
        q = self.db.query(Message).filter(Message.thread_id == thread_id)
        if before:
            ts: str = before
            if isinstance(ts, str) and ts.endswith("Z"):
                ts = ts.replace("Z", "+00:00")
            q = q.filter(Message.created_at < datetime.fromisoformat(ts))
        q = q.order_by(Message.created_at.desc()).limit(limit)
        rows = q.all()
        return [{
            "id": str(m.id), "role": m.role, "format": m.format, "content": m.content,
            "created_at": m.created_at.isoformat(), "parent_id": str(m.parent_id) if m.parent_id else None
        } for m in rows]
