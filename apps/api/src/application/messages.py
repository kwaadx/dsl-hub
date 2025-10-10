from __future__ import annotations

from ..app_decorators import instrument_uc
import uuid
from typing import Optional, Any, Dict, Iterable
from ..core.ports import MessageRepo, ThreadRepo
from ..core.uow import UnitOfWork
from ..core.errors import NotFound, ValidationFailed

ALLOWED_ROLES = {"user", "assistant", "system", "tool"}
ALLOWED_FORMATS = {"text", "markdown", "json", "buttons", "card"}

class CreateMessage:
    @instrument_uc('CreateMessage')
    def __init__(self, uow: UnitOfWork, messages: MessageRepo, threads: ThreadRepo):
        self.uow, self.messages, self.threads = uow, messages, threads
    def __call__(self, *, thread_id: str, role: str, content: Any, fmt: str = "text",
                 parent_id: Optional[str] = None, tool_name: Optional[str] = None, tool_result: Optional[Any] = None) -> Dict[str, Any]:
        if role not in ALLOWED_ROLES:
            raise ValidationFailed(f"Unsupported role: {role}")
        if fmt not in ALLOWED_FORMATS:
            raise ValidationFailed(f"Unsupported format: {fmt}")
        t = self.threads.get(thread_id)
        if not t:
            raise NotFound(f"Thread {thread_id} not found")
        msg_id = str(uuid.uuid4())
        m = self.messages.add(message_id=msg_id, thread_id=thread_id, role=role, content=content,
                              parent_id=parent_id, tool_name=tool_name, tool_result=tool_result, fmt=fmt)
        self.uow.commit()
        return {
            "id": m.id, "thread_id": m.thread_id, "role": m.role, "format": m.format, "content": m.content,
            "created_at": m.created_at, "parent_id": m.parent_id
        }

class ListMessages:
    @instrument_uc('ListMessages')
    def __init__(self, messages: MessageRepo):
        self.messages = messages
    def __call__(self, *, thread_id: str, before: Optional[str], limit: int) -> Iterable[Dict[str, Any]]:
        items = self.messages.list_window(thread_id, before, limit)
        return [{
            "id": m.id, "role": m.role, "format": m.format, "content": m.content,
            "created_at": m.created_at, "parent_id": m.parent_id
        } for m in items]