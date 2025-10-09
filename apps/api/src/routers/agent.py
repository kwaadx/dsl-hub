from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import Response
from typing import Union
from ..database import SessionLocal
from ..dto import AgentRunIn, AgentRunAck, SuggestionOut, UIEventIn, UIEventAck
from ..sse import sse_response, bus
from ..agent.graph import AgentRunner
from ..config import settings
from ..services.similarity_service import SimilarityService
from ..services.llm import LLMClient
from ..metrics import AGENT_RUNS
import asyncio, uuid

router = APIRouter(prefix="/threads", tags=["agent"])


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

@router.get("/{thread_id}/events")
async def sse_events(thread_id: str, request: Request) -> Response:
    last_id = request.headers.get("Last-Event-ID")
    if last_id:
        try:
            can = await bus.can_replay(thread_id, int(last_id))
        except ValueError:
            can = False
        if not can:
            return Response(status_code=204)
    return await sse_response(thread_id, ping_interval=settings.SSE_PING_INTERVAL, last_event_id=last_id)

@router.post("/{thread_id}/agent/run", response_model=Union[AgentRunAck, SuggestionOut])
async def agent_run(
    thread_id: str,
    payload: AgentRunIn,
    runner: AgentRunner = Depends(get_agent_runner),
) -> Union[AgentRunAck, SuggestionOut]:
    flow_id = await _infer_flow(thread_id)
    run_id = str(uuid.uuid4())

    # Fast-path: synchronous suggestion (MVP stop-after-suggestion)
    cand = runner.similarity.find_candidate(flow_id, payload.user_message)
    if cand:
        # Emit SSE lifecycle for suggestion-only run
        await bus.publish(thread_id, "run.started", {"run_id": run_id, "stage": "discovery"})
        await bus.publish(thread_id, "run.stage", {"run_id": run_id, "stage": "search_existing", "status": "running"})
        await bus.publish(thread_id, "run.stage", {"run_id": run_id, "stage": "search_existing", "status": "succeeded"})
        await bus.publish(thread_id, "suggestion", cand)
        try:
            AGENT_RUNS.labels(mode="suggestion").inc()
        except (ValueError, TypeError):
            # Ignore metrics errors but avoid broad exception suppression
            pass
        # Persist GenerationRun quickly
        db = runner.session_factory()
        try:
            runs = runner.runs_repo_factory(db)
            runs.start(run_id, flow_id, thread_id, stage="discovery", source=payload.user_message)
            runs.tick(run_id, stage="discovery", status="succeeded")
            runs.tick(run_id, stage="search_existing", status="succeeded", result={"suggestion": cand})
            runs.finish(run_id, status="succeeded")
            db.commit()
        finally:
            db.close()
        await bus.publish(thread_id, "run.finished", {"run_id": run_id, "status": "succeeded"})
        return SuggestionOut(ok=False, suggestion=cand)

    # Otherwise: enqueue full async FSM run and return ack
    try:
        AGENT_RUNS.labels(mode="fsm").inc()
    except (ValueError, TypeError):
        # Ignore metrics errors but avoid broad exception suppression
        pass
    # Acknowledge immediately
    asyncio.create_task(runner.run(flow_id, thread_id, payload.user_message, payload.options or {}, run_id=run_id))
    return AgentRunAck(run_id=run_id, status="queued")

async def _infer_flow(thread_id: str) -> str:
    from ..models import Thread
    db = SessionLocal()
    try:
        t = db.get(Thread, thread_id)
        if not t:
            raise HTTPException(status_code=404, detail="Thread not found")
        return str(t.flow_id)
    finally:
        db.close()

@router.post("/{thread_id}/agent/event", response_model=UIEventAck, status_code=202)
async def agent_event(thread_id: str, payload: UIEventIn) -> UIEventAck:
    """Accept UI events from the UI and acknowledge them via SSE.
    This does not advance the FSM for now; it simply reflects user actions in the stream.
    """
    kind = (payload.kind or "").lower()
    msg: str
    if kind == "action.click":
        aid = payload.actionId or ""
        msg = f'Action "{aid}" accepted' if aid else "Action accepted"
    elif kind == "choice.submit":
        value = None
        try:
            if isinstance(payload.payload, dict):
                value = payload.payload.get("value")
        except Exception:
            value = None
        msg = f'Choice "{value}" submitted' if value is not None else "Choice submitted"
    elif kind == "card.open":
        url = payload.url or ""
        msg = f"Open card {url}" if url else "Open card"
    else:
        msg = f"Event {payload.kind} received"

    await bus.publish(thread_id, "ui.ack", {"kind": payload.kind, "msg": msg, "event": payload.dict()})
    return UIEventAck(ok=True)
