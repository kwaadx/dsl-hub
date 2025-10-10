from __future__ import annotations

from typing import Optional, Iterable, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from ..models import Thread, Message
from ..core.entities import ThreadEntity, MessageEntity

def _t(row: Thread) -> ThreadEntity:
    return ThreadEntity(
        id=str(row.id), flow_id=row.flow_id, status=row.status,
        started_at=row.started_at.isoformat() if row.started_at else "",
        closed_at=row.closed_at.isoformat() if row.closed_at else None,
    )

def _m(row: Message) -> MessageEntity:
    return MessageEntity(
        id=str(row.id), thread_id=row.thread_id, role=row.role, format=row.format,
        content=row.content, created_at=row.created_at.isoformat(),
        parent_id=str(row.parent_id) if row.parent_id else None
    )

class SAThreadRepo:
    def __init__(self, db: Session): self.db = db
    def get(self, thread_id: str) -> Optional[ThreadEntity]:
        row = self.db.get(Thread, thread_id)
        return _t(row) if row else None
    def create_if_missing(self, thread_id: str, flow_id: str) -> ThreadEntity:
        row = self.db.get(Thread, thread_id)
        if row: return _t(row)
        row = Thread(id=thread_id, flow_id=flow_id, status="NEW")
        self.db.add(row); self.db.flush()
        return _t(row)

class SAMessageRepo:
    def __init__(self, db: Session): self.db = db
    def add(self, *, message_id: str, thread_id: str, role: str, content: Any, 
            parent_id: Optional[str], tool_name: Optional[str], tool_result: Optional[Any], fmt: str):
        m = Message(id=message_id, thread_id=thread_id, role=role, content=content,
                    parent_id=parent_id, tool_name=tool_name, tool_result=tool_result, format=fmt)
        self.db.add(m); self.db.flush(); self.db.refresh(m)
        return _m(m)
    def list_for_thread(self, thread_id: str, limit: int = 50) -> Iterable[MessageEntity]:
        q = self.db.query(Message).filter(Message.thread_id==thread_id).order_by(Message.created_at.asc()).limit(limit)
        return [_m(r) for r in q.all()]
    def list_window(self, thread_id: str, before: Optional[str], limit: int) -> Iterable[MessageEntity]:
        q = self.db.query(Message).filter(Message.thread_id==thread_id)
        if before:
            from datetime import datetime
            ts = before.replace("Z", "+00:00")
            cutoff = datetime.fromisoformat(ts)
            q = q.filter(Message.created_at < cutoff)
        q = q.order_by(Message.created_at.desc()).limit(limit)
        return [_m(r) for r in q.all()]