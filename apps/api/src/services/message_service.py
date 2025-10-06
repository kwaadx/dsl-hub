import uuid
from datetime import datetime
from typing import Any, Optional, List, Dict

from sqlalchemy.orm import Session

from ..middleware.error import AppError
from ..models import Thread
from ..repositories.message_repo import MessageRepo

ALLOWED_ROLES = {"user", "assistant", "system", "tool"}
ALLOWED_FORMATS = {"text", "markdown", "json", "buttons", "card"}

class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MessageRepo(db)

    def _require_thread(self, thread_id: str) -> Thread:
        thread = self.db.get(Thread, thread_id)
        if thread is None:
            raise AppError(status=404, code="THREAD_NOT_FOUND", message="Thread not found")
        return thread

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
        thread = self._require_thread(thread_id)
        if getattr(thread, "archived", False):
            raise AppError(status=409, code="THREAD_ARCHIVED", message="Thread is archived")
        if getattr(thread, "closed_at", None):
            raise AppError(status=409, code="THREAD_CLOSED", message="Thread is closed")

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
        self._require_thread(thread_id)
        from ..models import Message
        if limit <= 0 or limit > 200:
            raise AppError(status=400, code="BAD_LIMIT", message="limit must be between 1 and 200")
        q = self.db.query(Message).filter(Message.thread_id == thread_id)
        if before:
            ts = before
            if not isinstance(ts, str):
                raise AppError(status=400, code="BAD_BEFORE_CURSOR", message="before must be an ISO timestamp string")
            if ts.endswith("Z"):
                ts = ts.replace("Z", "+00:00")
            try:
                cutoff = datetime.fromisoformat(ts)
            except ValueError as exc:
                raise AppError(status=400, code="BAD_BEFORE_CURSOR", message="Invalid before timestamp") from exc
            q = q.filter(Message.created_at < cutoff)
        q = q.order_by(Message.created_at.desc()).limit(limit)
        rows = q.all()
        return [{
            "id": str(m.id), "role": m.role, "format": m.format, "content": m.content,
            "created_at": m.created_at.isoformat(), "parent_id": str(m.parent_id) if m.parent_id else None
        } for m in rows]
