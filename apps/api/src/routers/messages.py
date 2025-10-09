from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select, and_, or_, asc

from ..database import SessionLocal
from ..models import Message, Thread
from ..sse import bus
from ..dto import MessageIn
from ..services.similarity_service import SimilarityService
from ..services.llm import LLMClient
from ..agent.graph import AgentRunner
from ..metrics import MESSAGES_CREATED
from ..config import settings

router = APIRouter(prefix="/threads", tags=["messages"])  # keep same namespace under /threads


# ---- Agent dependencies (copied from agent router) ----

def get_similarity_service() -> SimilarityService:
    return SimilarityService()


def get_llm_client() -> LLMClient:
    return LLMClient()


def get_agent_runner(
    similarity: SimilarityService = Depends(get_similarity_service),
    llm: LLMClient = Depends(get_llm_client),
) -> AgentRunner:
    return AgentRunner(
        session_factory=SessionLocal,
        similarity_service=similarity,
        llm_client=llm,
    )


# ---- Helpers ----

# Simple in-memory rate limiter per thread (sliding 60s window)
_RATE_BUCKETS: dict[str, list[float]] = {}

def _check_rate_limit(thread_id: str) -> None:
    import time
    limit = max(0, int(getattr(settings, "MESSAGES_RATE_PER_MINUTE", 30)))
    if limit <= 0:
        return  # disabled
    now = time.time()
    window = 60.0
    bucket = _RATE_BUCKETS.setdefault(thread_id, [])
    # prune old timestamps
    cutoff = now - window
    i = 0
    for ts in bucket:
        if ts >= cutoff:
            break
        i += 1
    if i:
        del bucket[:i]
    if len(bucket) >= limit:
        # 429 Too Many Requests
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded: max {limit} messages per minute for this thread")
    bucket.append(now)


def _to_msg_out(m: Message) -> Dict[str, Any]:
    created_at = None
    try:
        if getattr(m, "created_at", None) is not None:
            created_at = m.created_at.isoformat()
    except Exception:
        created_at = None
    return {
        "id": str(m.id),
        "role": m.role,
        "format": m.format,
        "content": m.content,
        "created_at": created_at,
        "parent_id": (str(m.parent_id) if getattr(m, "parent_id", None) else None),
        "tool_name": getattr(m, "tool_name", None),
        "tool_result": getattr(m, "tool_result", None),
    }


async def _infer_flow(thread_id: str) -> str:
    db = SessionLocal()
    try:
        t = db.get(Thread, thread_id)
        if not t:
            raise HTTPException(status_code=404, detail="Thread not found")
        return str(t.flow_id)
    finally:
        db.close()


# ---- Routes ----

@router.get("/{thread_id}/messages")
async def list_messages(
    thread_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    before: Optional[str] = Query(default=None, description="Cursor: message id to fetch items strictly older than"),
    response: Response = None,
) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        # Ensure thread exists
        t = db.get(Thread, thread_id)
        if not t:
            raise HTTPException(status_code=404, detail="Thread not found")

        base_q = select(Message).where(Message.thread_id == thread_id)
        cur = None
        if before:
            # Try to resolve cursor by id
            cur = db.get(Message, before)
            if cur is not None and getattr(cur, "created_at", None) is not None:
                base_q = base_q.where(
                    or_(
                        Message.created_at < cur.created_at,
                        and_(Message.created_at == cur.created_at, Message.id < cur.id),
                    )
                )
        q = base_q.order_by(asc(Message.created_at), asc(Message.id)).limit(limit)
        rows = db.execute(q).scalars().all()

        # Pagination hint header: X-Next-Cursor (older messages)
        # If there are older messages than the first item in this page, set header to that first item's id
        if response is not None and rows:
            first = rows[0]
            # Check existence of any message older than the first item
            exists_q = (
                select(Message.id)
                .where(Message.thread_id == thread_id)
                .where(
                    or_(
                        Message.created_at < first.created_at,
                        and_(Message.created_at == first.created_at, Message.id < first.id),
                    )
                )
                .limit(1)
            )
            older = db.execute(exists_q).first()
            if older is not None:
                response.headers["X-Next-Cursor"] = str(first.id)
        return [_to_msg_out(m) for m in rows]
    finally:
        db.close()


@router.post("/{thread_id}/messages", status_code=201)
async def create_message(
    thread_id: str,
    payload: MessageIn,
    request: Request,
    run: Optional[int] = Query(default=0, description="When 1, start agent FSM after creating the message"),
    runner: AgentRunner = Depends(get_agent_runner),
) -> Dict[str, Any]:
    if (payload.role or "").lower() != "user":
        raise HTTPException(status_code=400, detail="Only role=user is supported for POST /messages")

    # Per-thread rate limit (Stage 12)
    _check_rate_limit(thread_id)

    # Content length validation (Stage 12)
    try:
        max_len = int(getattr(settings, "MESSAGE_TEXT_MAX_LEN", 4000))
    except (ValueError, TypeError):
        max_len = 4000
    fmt = (getattr(payload, "format", "text") or "text").lower()
    content = getattr(payload, "content", None)
    if fmt in ("text", "markdown"):
        # content can be a dict with text field or a raw string
        text_value = None
        if isinstance(content, dict):
            tv = content.get("text") if hasattr(content, "get") else None
            if isinstance(tv, str):
                text_value = tv
        elif isinstance(content, str):
            text_value = content
        if text_value is not None and len(text_value) > max_len:
            raise HTTPException(status_code=413, detail=f"Message content too large (max {max_len} chars)")

    db = SessionLocal()
    try:
        # Validate thread
        t = db.get(Thread, thread_id)
        if not t:
            raise HTTPException(status_code=404, detail="Thread not found")

        msg_id = str(uuid.uuid4())
        m = Message(
            id=msg_id,
            thread_id=thread_id,
            role=payload.role,
            format=payload.format or "text",
            parent_id=payload.parent_id,
            tool_name=payload.tool_name,
            tool_result=payload.tool_result,
            content=payload.content,
        )
        db.add(m)
        db.flush()
        # refresh to obtain created_at
        try:
            db.refresh(m)
        except Exception:
            pass
        db.commit()

        # Emit SSE for the created user message (so other clients see it as well)
        try:
            await bus.publish(thread_id, "message.created", {
                "message_id": msg_id,
                "role": m.role,
                "format": m.format,
                "content": m.content,
            })
        except Exception:
            # SSE failures should not break the API response
            pass
        # Metrics: count created user messages via route
        try:
            if MESSAGES_CREATED is not None:
                MESSAGES_CREATED.labels(role=str(m.role), source="route").inc()
        except (ValueError, TypeError, RuntimeError):
            pass

        meta: Dict[str, Any] = {}
        if run == 1:
            # Start FSM using the just created message as the user_message
            flow_id = await _infer_flow(thread_id)
            run_id = str(uuid.uuid4())
            # Fire and forget
            import asyncio
            asyncio.create_task(
                runner.run(flow_id, thread_id, {"role": m.role, "format": m.format, "content": m.content}, {}, run_id=run_id)
            )
            meta["run"] = {"run_id": run_id, "status": "queued"}

        out = _to_msg_out(m)
        if meta:
            out = {**out, "meta": meta}
        return out
    finally:
        db.close()