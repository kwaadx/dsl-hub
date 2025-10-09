from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, UTC
import uuid

from ..middleware.error import AppError
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
            raise AppError(status=404, code="THREAD_NOT_FOUND", message="Thread not found")
        # Collect messages for summarization (MVP: whole thread)
        messages_payload = self._collect_messages_payload(thread_id)
        # Call LLM to summarize
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

    def get_last_message_id(self, thread_id: str) -> str | None:
        """Return the last message id for a thread, or None if no messages."""
        _, _, last = self._messages_bounds(thread_id)
        return last

    async def close_thread(self, thread_id: str) -> Dict[str, Any]:
        """Atomically close a thread and update flow summary.
        Idempotent: if thread is already closed, do not create new summaries and return the latest ones.
        """
        t = self.db.get(Thread, thread_id)
        if not t:
            raise AppError(status=404, code="THREAD_NOT_FOUND", message="Thread not found")
        # If already closed, return latest existing summary info without side effects
        if getattr(t, "closed_at", None):
            # Latest thread summary
            last_ts = self.db.execute(
                select(ThreadSummary).where(ThreadSummary.thread_id == thread_id).order_by(ThreadSummary.created_at.desc()).limit(1)
            ).scalar_one_or_none()
            # Active flow summary
            from ..repositories.flow_summary_repo import get_active as get_active_flow_summary
            fs = get_active_flow_summary(self.db, str(t.flow_id))
            return dict(
                ok=True,
                thread_id=thread_id,
                thread_summary_id=str(last_ts.id) if last_ts else None,
                flow_summary=dict(id=str(fs.id), version=fs.version) if fs else dict(id=None, version=0),
            )
        # Summarize thread
        ts = await self.run_thread_summary(thread_id)
        # Compute last message id once
        last_message_id = self.get_last_message_id(thread_id)
        # Upsert flow summary and ensure single active
        fs = self.upsert_flow_summary(str(t.flow_id), last_message_id=last_message_id,
                                      new_content={"summary": ts.content.get("summary", "")})
        self.ensure_single_active(str(t.flow_id), str(fs.id))
        # Close thread
        t.status = "SUCCESS"
        t.closed_at = datetime.now(UTC)
        self.db.flush()
        return dict(
            ok=True,
            thread_id=thread_id,
            thread_summary_id=str(ts.id),
            flow_summary=dict(id=str(fs.id), version=fs.version)
        )
