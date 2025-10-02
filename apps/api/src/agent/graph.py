
from __future__ import annotations

import uuid
from typing import TypedDict, Optional, Dict, Any

from langgraph.graph import START, END, StateGraph

from ..sse import bus
from ..database import SessionLocal
from ..repositories.runs_repo import RunsRepo
from ..services.validation_service import ValidationService
from ..services.pipeline_service import PipelineService
from ..services.similarity_service import SimilarityService
from ..services.llm import LLMClient


class AgentState(TypedDict, total=False):
    flow_id: str
    thread_id: str
    user_message: dict
    options: dict
    run_id: str
    # results accumulating
    candidate: Optional[dict]
    draft: Optional[dict]
    notes: Optional[dict]
    issues: Optional[list]
    persisted: Optional[dict]
    will_publish: bool


class AgentRunner:
    """LangGraph-powered agent runner.
    Each node pushes SSE events and updates generation_run via RunsRepo.
    """
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        self.similarity = SimilarityService()
        self.llm = LLMClient()

    def _gather_context(self, flow_id: str) -> Dict[str, Any]:
        from sqlalchemy import select
        from ..models import SchemaChannel, FlowSummary, Pipeline
        from ..config import settings
        db = self.session_factory()
        try:
            ch = db.execute(select(SchemaChannel).where(SchemaChannel.name==settings.APP_SCHEMA_CHANNEL)).scalar_one_or_none()
            schema_def = ch.active_schema.json if ch and ch.active_schema else {}
            fs = db.execute(select(FlowSummary).where(FlowSummary.flow_id==flow_id, FlowSummary.is_active==True).limit(1)).scalar_one_or_none()
            ap = db.execute(select(Pipeline).where(Pipeline.flow_id==flow_id, Pipeline.is_published==True).limit(1)).scalar_one_or_none()
            return {
                "schema_def": schema_def,
                "flow_summary": (fs.content if fs else None),
                "active_pipeline": (ap.content if ap else None),
            }
        finally:
            db.close()

    async def run(self, flow_id: str, thread_id: str, user_message: Dict[str, Any], options: Dict[str, Any] | None = None, run_id: str | None = None) -> str:
        run_id = run_id or str(uuid.uuid4())
        # compose state
        state: AgentState = {
            "flow_id": flow_id,
            "thread_id": thread_id,
            "user_message": user_message,
            "options": options or {},
            "run_id": run_id,
            "will_publish": bool((options or {}).get("publish", False))
        }

        # Build LangGraph
        graph = StateGraph(AgentState)

        # --- nodes ---
        async def init_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.started", {"run_id": s["run_id"], "stage": "discovery"})
            db = self.session_factory()
            runs = RunsRepo(db)
            runs.start(s["run_id"], s["flow_id"], s["thread_id"], stage="discovery", source=s["user_message"]) 
            runs.tick(s["run_id"], stage="discovery", status="succeeded")
            db.commit()
            db.close()
            return s

        async def search_existing(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "search_existing", "status": "running"})
            cand = self.similarity.find_candidate(s["flow_id"], s["user_message"])
            s["candidate"] = cand
            # persist stage
            db = self.session_factory(); runs = RunsRepo(db)
            runs.tick(s["run_id"], stage="search_existing", status="succeeded")
            db.commit()
            db.close()
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "search_existing", "status": "succeeded"})
            if cand:
                await bus.publish(s["thread_id"], "suggestion", cand)
            return s

        def decide_after_suggestion(s: AgentState) -> str:
            # MVP behavior: if candidate exists, stop and let user decide in UI
            return "finish" if s.get("candidate") else "generate"

        async def generate_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "generate", "status": "running"})
            # gather context for LLM
            ctx = self._gather_context(s["flow_id"]) 
            draft = await self.llm.generate_pipeline(ctx, s["user_message"])
            s["draft"] = draft
            db = self.session_factory(); runs = RunsRepo(db)
            runs.tick(s["run_id"], stage="generate", status="succeeded", result={"draft_head": list(draft.keys())})
            db.commit()
            db.close()
            await bus.publish(s["thread_id"], "agent.msg", {"role":"assistant","format":"markdown","content":{"text":"Генерую пайплайн…"}})
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "generate", "status": "succeeded"})
            return s

        async def self_check_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "self_check", "status": "running"})
            notes = await self.llm.self_check(s["draft"] or {})
            s["notes"] = notes
            db = self.session_factory(); runs = RunsRepo(db)
            runs.tick(s["run_id"], stage="self_check", status="succeeded", result={"notes": notes})
            db.commit()
            db.close()
            await bus.publish(s["thread_id"], "agent.msg", {"role":"assistant","format":"markdown","content":{"text":"Перевіряю узгодженість…"}})
            await bus.publish(s["thread_id"], "agent.msg", {"role":"assistant","format":"json","content": s["notes"]})
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "self_check", "status": "succeeded"})
            return s

        async def hard_validate_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "hard_validate", "status": "running"})
            db = self.session_factory()
            validator = ValidationService(db)
            issues = validator.validate_pipeline(s["draft"] or {})
            s["issues"] = issues
            runs = RunsRepo(db)
            status = "failed" if issues else "succeeded"
            runs.tick(s["run_id"], stage="hard_validate", status=status, result={"issues": issues})
            if issues:
                runs.add_issues(s["run_id"], issues)
            db.commit()
            db.close()
            if issues:
                await bus.publish(s["thread_id"], "issues", {"items": issues})
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "hard_validate", "status": status})
            return s

        def has_issues(s: AgentState) -> str:
            return "finish" if s.get("issues") else "persist"

        async def persist_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "persist", "status": "running"})
            db = self.session_factory()
            pipelines = PipelineService(db)
            p = pipelines.create_version(s["flow_id"], s.get("draft") or {})
            s["persisted"] = {"pipeline_id": str(p.id), "version": p.version}
            runs = RunsRepo(db); runs.tick(s["run_id"], stage="persist", status="succeeded")
            db.commit()
            db.close()
            await bus.publish(s["thread_id"], "pipeline.created", {"pipeline_id": str(p.id), "version": p.version, "status": p.status})
            return s

        def should_publish(s: AgentState) -> str:
            return "publish" if s.get("will_publish") else "finish"

        async def publish_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage", {"run_id": s["run_id"], "stage": "publish", "status": "running"})
            db = self.session_factory()
            pipelines = PipelineService(db)
            if s.get("persisted"):
                pipelines.publish(s["persisted"]["pipeline_id"])
                await bus.publish(s["thread_id"], "pipeline.published", {"pipeline_id": s["persisted"]["pipeline_id"], "version": s["persisted"]["version"]})
            runs = RunsRepo(db); runs.tick(s["run_id"], stage="publish", status="succeeded")
            db.commit()
            db.close()
            return s

        async def finish_node(s: AgentState) -> AgentState:
            status = "failed" if s.get("issues") else "succeeded"
            db = self.session_factory(); runs = RunsRepo(db)
            runs.finish(s["run_id"], status=status)
            db.commit()
            db.close()
            await bus.publish(s["thread_id"], "run.finished", {"run_id": s["run_id"], "status": status})
            return s

        # Register nodes
        graph.add_node("init", init_node)
        graph.add_node("search_existing", search_existing)
        graph.add_node("generate", generate_node)
        graph.add_node("self_check", self_check_node)
        graph.add_node("hard_validate", hard_validate_node)
        graph.add_node("persist", persist_node)
        graph.add_node("publish", publish_node)
        graph.add_node("finish", finish_node)

        # Edges
        graph.add_edge(START, "init")
        graph.add_edge("init", "search_existing")
        graph.add_conditional_edges("search_existing", decide_after_suggestion, {"finish": "finish", "generate": "generate"})
        graph.add_edge("generate", "self_check")
        graph.add_edge("self_check", "hard_validate")
        graph.add_conditional_edges("hard_validate", has_issues, {"finish": "finish", "persist": "persist"})
        graph.add_conditional_edges("persist", should_publish, {"publish": "publish", "finish": "finish"})
        graph.add_edge("publish", "finish")
        graph.add_edge("finish", END)

        # Compile and execute
        app = graph.compile()
        # run the graph asynchronously
        try:
            await app.ainvoke(state)  # we stream via SSE inside nodes
        except Exception as e:
            # Ensure we mark the run as failed and emit a terminal event
            db = self.session_factory()
            try:
                runs = RunsRepo(db)
                try:
                    runs.finish(run_id, status="failed")
                    db.commit()
                except Exception:
                    db.rollback()
            finally:
                db.close()
            await bus.publish(thread_id, "run.finished", {"run_id": run_id, "status": "failed", "error": str(e)})
            return run_id
        return run_id
