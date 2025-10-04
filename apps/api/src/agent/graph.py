from __future__ import annotations

import uuid
from typing import TypedDict, Optional, Dict, Any, cast

from langgraph.graph import START, END, StateGraph
from sqlalchemy.exc import SQLAlchemyError

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
    user_message: Dict[str, Any]
    options: Dict[str, Any]
    run_id: str
    # results accumulating
    candidate: Optional[Dict[str, Any]]
    draft: Optional[Dict[str, Any]]
    notes: Optional[Dict[str, Any]]
    issues: Optional[list[Any]]
    persisted: Optional[Dict[str, Any]]
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
        from ..models import SchemaChannel, Pipeline
        from ..repositories.flow_summary_repo import get_active as get_active_flow_summary
        from ..config import settings
        db = self.session_factory()
        try:
            ch = db.execute(
                select(SchemaChannel).where(SchemaChannel.name == settings.SCHEMA_CHANNEL)).scalar_one_or_none()
            schema_def = ch.active_schema.json if ch and ch.active_schema else {}
            fs = get_active_flow_summary(db, flow_id)
            ap = db.execute(select(Pipeline).where(Pipeline.flow_id == flow_id, Pipeline.is_published == True).limit(
                1)).scalar_one_or_none()
            return dict(
                schema_def=schema_def,
                flow_summary=(fs.content if fs else None),
                active_pipeline=(ap.content if ap else None),
            )
        finally:
            db.close()

    async def run(self, flow_id: str, thread_id: str, user_message: Dict[str, Any],
                  options: Dict[str, Any] | None = None, run_id: str | None = None) -> str:
        run_id_str: str = run_id or str(uuid.uuid4())
        opts: Dict[str, Any] = options if options is not None else {}
        state: AgentState = {
            "flow_id": flow_id,
            "thread_id": thread_id,
            "user_message": user_message,
            "options": opts,
            "run_id": run_id_str,
            "will_publish": bool(opts.get("publish", False))
        }

        # Build LangGraph
        graph = StateGraph(AgentState)  # type: ignore[arg-type]

        # helpers to reduce duplication
        def _with_repo(op):
            session_factory = self.session_factory()
            try:
                repo = RunsRepo(session_factory)
                op(repo)
                session_factory.commit()
            finally:
                session_factory.close()

        def _tick(stage: str, status: str, result: Dict[str, Any] | None = None) -> None:
            def apply(repo: RunsRepo) -> None:
                repo.tick(run_id_str, stage=stage, status=status, result=result)

            _with_repo(apply)

        # --- nodes ---
        async def init_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.started", {"run_id": s["run_id"], "stage": "discovery"})
            session_factory = self.session_factory()
            runs_repo = RunsRepo(session_factory)
            runs_repo.start(s["run_id"], s["flow_id"], s["thread_id"], stage="discovery", source=s["user_message"])
            runs_repo.tick(s["run_id"], stage="discovery", status="succeeded")
            session_factory.commit()
            session_factory.close()
            return s

        async def search_existing(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "search_existing", "status": "running"})
            cand = self.similarity.find_candidate(s["flow_id"], s["user_message"])
            s["candidate"] = cand
            # persist stage
            _tick("search_existing", "succeeded")
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "search_existing", "status": "succeeded"})
            if cand:
                await bus.publish(s["thread_id"], "suggestion", cand)
            return s

        def decide_after_suggestion(s: AgentState) -> str:
            # MVP behavior: if candidate exists, stop and let user decide in UI
            return "finish" if s.get("candidate") else "generate"

        async def generate_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "generate", "status": "running"})
            # gather context for LLM
            ctx = self._gather_context(s["flow_id"])
            draft = await self.llm.generate_pipeline(ctx, s["user_message"])
            s["draft"] = draft
            _tick("generate", "succeeded", result={"draft_head": list(draft.keys())})
            await bus.publish(s["thread_id"], "agent.msg",
                              {"role": "assistant", "format": "markdown", "content": {"text": "Generating pipeline..."}})
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "generate", "status": "succeeded"})
            return s

        async def self_check_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "self_check", "status": "running"})
            draft_in = cast(Dict[str, Any], s.get("draft") or {})
            notes = await self.llm.self_check(draft_in)
            s["notes"] = notes
            _tick("self_check", "succeeded", result={"notes": notes})
            await bus.publish(s["thread_id"], "agent.msg", {"role": "assistant", "format": "markdown",
                                                            "content": {"text": "Checking consistency..."}})
            await bus.publish(s["thread_id"], "agent.msg", {"role": "assistant", "format": "json",
                                                            "content": cast(Dict[str, Any], s.get("notes") or {})})
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "self_check", "status": "succeeded"})
            return s

        async def hard_validate_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "hard_validate", "status": "running"})
            session_factory = self.session_factory()
            validator = ValidationService(session_factory)
            draft_in = cast(Dict[str, Any], s.get("draft") or {})
            issues = validator.validate_pipeline(draft_in)
            s["issues"] = issues
            runs_repo = RunsRepo(session_factory)
            status = "failed" if issues else "succeeded"
            runs_repo.tick(s["run_id"], stage="hard_validate", status=status, result={"issues": issues})
            if issues:
                runs_repo.add_issues(s["run_id"], issues)
            session_factory.commit()
            session_factory.close()
            if issues:
                await bus.publish(s["thread_id"], "issues", {"items": issues})
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "hard_validate", "status": status})
            return s

        def has_issues(s: AgentState) -> str:
            return "finish" if s.get("issues") else "persist"

        async def persist_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "persist", "status": "running"})
            session_factory = self.session_factory()
            pipelines = PipelineService(session_factory)
            content = cast(Dict[str, Any], s.get("draft") or {})
            p = pipelines.create_version(s["flow_id"], content)
            version_str = str(p.version) if getattr(p, "version", None) is not None else ""
            s["persisted"] = {"pipeline_id": str(p.id), "version": version_str}
            _tick("persist", "succeeded")
            await bus.publish(s["thread_id"], "pipeline.created",
                              {"pipeline_id": str(p.id), "version": version_str, "status": p.status})
            return s

        def should_publish(s: AgentState) -> str:
            return "publish" if s.get("will_publish") else "finish"

        async def publish_node(s: AgentState) -> AgentState:
            await bus.publish(s["thread_id"], "run.stage",
                              {"run_id": s["run_id"], "stage": "publish", "status": "running"})
            session_factory = self.session_factory()
            pipelines = PipelineService(session_factory)
            if s.get("persisted"):
                pipelines.publish(s["persisted"]["pipeline_id"])
                await bus.publish(s["thread_id"], "pipeline.published",
                                  {"pipeline_id": s["persisted"]["pipeline_id"], "version": s["persisted"]["version"]})
            _tick("publish", "succeeded")
            return s

        async def finish_node(s: AgentState) -> AgentState:
            status = "failed" if s.get("issues") else "succeeded"
            session_factory = self.session_factory()
            runs_repo = RunsRepo(session_factory)
            runs_repo.finish(s["run_id"], status=status)
            session_factory.commit()
            session_factory.close()
            await bus.publish(s["thread_id"], "run.finished", {"run_id": s["run_id"], "status": status})
            return s

        # Register nodes
        graph.add_node("init", init_node)  # type: ignore[arg-type]
        graph.add_node("search_existing", search_existing)  # type: ignore[arg-type]
        graph.add_node("generate", generate_node)  # type: ignore[arg-type]
        graph.add_node("self_check", self_check_node)  # type: ignore[arg-type]
        graph.add_node("hard_validate", hard_validate_node)  # type: ignore[arg-type]
        graph.add_node("persist", persist_node)  # type: ignore[arg-type]
        graph.add_node("publish", publish_node)  # type: ignore[arg-type]
        graph.add_node("finish", finish_node)  # type: ignore[arg-type]

        # Edges
        graph.add_edge(START, "init")
        graph.add_edge("init", "search_existing")
        graph.add_conditional_edges("search_existing", decide_after_suggestion,
                                    {"finish": "finish", "generate": "generate"})
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
        except Exception as e:  # noqa: BLE001
            # Ensure we mark the run as failed and emit a terminal event
            db_session = self.session_factory()
            try:
                runs = RunsRepo(db_session)
                try:
                    runs.finish(run_id_str, status="failed")
                    db_session.commit()
                except SQLAlchemyError:
                    db_session.rollback()
            finally:
                db_session.close()
            await bus.publish(thread_id, "run.finished", {"run_id": run_id_str, "status": "failed", "error": str(e)})
            return run_id_str
        return run_id_str
