from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from ..database import get_db, SessionLocal
from ..dto import AgentRunIn, AgentRunAck
from ..sse import sse_response, bus
from ..agent.graph import AgentRunner
from ..config import settings
import asyncio, uuid

router = APIRouter(prefix="/threads", tags=["agent"]) 

@router.get("/{thread_id}/events")
async def sse_events(thread_id: str, request: Request):
    last_id = request.headers.get("Last-Event-ID")
    if last_id:
        try:
            can = await bus.can_replay(thread_id, int(last_id))
        except Exception:
            can = False
        if not can:
            return Response(status_code=204)
    return await sse_response(thread_id, ping_interval=settings.SSE_PING_INTERVAL, last_event_id=last_id)

@router.post("/{thread_id}/agent/run", response_model=AgentRunAck)
async def agent_run(thread_id: str, payload: AgentRunIn):
    flow_id = await _infer_flow(thread_id)
    run_id = str(uuid.uuid4())  # acknowledge immediately
    # Fire-and-forget background task
    asyncio.create_task(AgentRunner(SessionLocal).run(flow_id, thread_id, payload.user_message, payload.options or {}, run_id=run_id))
    return {"run_id": run_id, "status": "queued"}

async def _infer_flow(thread_id: str) -> str:
    # minimal lookup
    from sqlalchemy import select
    from ..models import Thread
    db = SessionLocal()
    try:
        t = db.get(Thread, thread_id)
        return str(t.flow_id)
    finally:
        db.close()
