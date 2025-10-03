from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, UTC
import uuid

from ..models import Thread, Message, ThreadSummary, FlowSummary
from ..services.llm import LLMClient


class SummaryService:
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMClient()

    def _messages_bounds(self, thread_id: str) -> Tuple[Optional[datetime], Optional[datetime], Optional[str]]:
        """Return covering_from, covering_to, last_message_id for a thread.
        None-safe if no messages.
        """
        # newest first to get last message quickly
        q = self.db.execute(
            select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at.desc())
        ).scalars().all()
        if not q:
            return None, None, None
        newest = q[0]
        oldest = q[-1]
        return oldest.created_at, newest.created_at, str(newest.id)

    def _collect_messages_payload(self, thread_id: str) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at.asc())
        ).scalars().all()
        out: List[Dict[str, Any]] = []
        for m in rows:
            out.append({
                "id": str(m.id),
                "role": m.role,
                "format": m.format,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            })
        return out

    async def run_thread_summary(self, thread_id: str) -> ThreadSummary:
        t = self.db.get(Thread, thread_id)
        if not t:
            raise ValueError("Thread not found")
        # Collect messages for summarization (MVP: whole thread)
        messages_payload = self._collect_messages_payload(thread_id)
        # Call LLM to summarize (mock by default)
        data = await self.llm.summarize({
            "thread_id": thread_id,
            "flow_id": str(t.flow_id),
            "messages": messages_payload,
        })
        covering_from, covering_to, _ = self._messages_bounds(thread_id)
        ts = ThreadSummary(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            kind="short",
            content=data,
            covering_from=covering_from,
            covering_to=covering_to,
        )
        self.db.add(ts)
        self.db.flush()
        return ts

    def upsert_flow_summary(self, flow_id: str, last_message_id: Optional[str] = None, new_content: Optional[Dict[str, Any]] = None) -> FlowSummary:
        # Find active summary for this flow
        fs: Optional[FlowSummary] = self.db.execute(
            select(FlowSummary).where(FlowSummary.flow_id == flow_id, FlowSummary.is_active == True).limit(1)  # noqa: E712
        ).scalar_one_or_none()
        if fs:
            fs.version = int(fs.version or 0) + 1
            if new_content is not None:
                fs.content = new_content
            if last_message_id:
                fs.last_message_id = last_message_id
            fs.is_active = True
            self.db.flush()
            return fs
        # Otherwise, create a new active summary with minimal content
        fs = FlowSummary(
            id=str(uuid.uuid4()),
            flow_id=flow_id,
            version=1,
            content=new_content or {"summary": ""},
            last_message_id=last_message_id,
            is_active=True,
        )
        self.db.add(fs)
        self.db.flush()
        return fs

    def ensure_single_active(self, flow_id: str, active_id: str) -> None:
        """Ensure only one active summary for the flow by clearing flags on others."""
        self.db.query(FlowSummary).\
            filter(FlowSummary.flow_id == flow_id, FlowSummary.id != active_id, FlowSummary.is_active == True).\
            update({"is_active": False})
        self.db.flush()
