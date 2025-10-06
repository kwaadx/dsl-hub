import asyncio
from types import SimpleNamespace

import apps.api.src.agent.graph as agent_graph
from apps.api.src.agent.graph import AgentRunner


class _FakeBus:
    def __init__(self):
        self.events: list[tuple[str, str, dict]] = []

    async def publish(self, key: str, event_type: str, data):
        self.events.append((key, event_type, data))


class _FakeSimilarity:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def find_candidate(self, flow_id: str, user_message: dict):
        self.calls.append((flow_id, user_message))
        return None


class _FakeLLM:
    def __init__(self):
        self.generated: list[tuple[dict, dict]] = []
        self.checked: list[dict] = []

    async def generate_pipeline(self, context: dict, user_message: dict):
        self.generated.append((context, user_message))
        return {"stages": [], "meta": "draft"}

    async def self_check(self, draft: dict):
        self.checked.append(draft)
        return {"notes": ["ok"], "risks": []}


class _FakeValidation:
    def __init__(self):
        self.requests: list[dict] = []

    def validate_pipeline(self, pipeline: dict):
        self.requests.append(pipeline)
        return []


class _FakePipelineService:
    def __init__(self):
        self.created: list[tuple[str, dict]] = []
        self.published: list[str] = []

    def create_version(self, flow_id: str, content: dict):
        self.created.append((flow_id, content))
        return SimpleNamespace(id="pip-1", version="1.0.0", status="draft")

    def publish(self, pipeline_id: str):
        self.published.append(pipeline_id)
        return {"ok": True}


class _FakeRunsRepo:
    def __init__(self):
        self.records: list[tuple[str, tuple, dict]] = []

    def start(self, *args, **kwargs):
        self.records.append(("start", args, kwargs))

    def tick(self, *args, **kwargs):
        self.records.append(("tick", args, kwargs))

    def finish(self, *args, **kwargs):
        self.records.append(("finish", args, kwargs))

    def add_issues(self, *args, **kwargs):
        self.records.append(("add_issues", args, kwargs))


class _FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed += 1


def test_agent_runner_uses_injected_dependencies(monkeypatch):
    fake_bus = _FakeBus()
    monkeypatch.setattr(agent_graph, "bus", fake_bus, raising=False)

    similarity = _FakeSimilarity()
    llm = _FakeLLM()
    validation_service = _FakeValidation()
    pipeline_service = _FakePipelineService()
    runs_repo_instances: list[_FakeRunsRepo] = []
    sessions: list[_FakeSession] = []

    def _session_factory():
        session = _FakeSession()
        sessions.append(session)
        return session

    def _runs_repo_factory(session):
        repo = _FakeRunsRepo()
        runs_repo_instances.append(repo)
        return repo

    def _validation_factory(session):
        return validation_service

    def _pipeline_factory(session):
        return pipeline_service

    runner = AgentRunner(
        session_factory=_session_factory,
        similarity_service=similarity,
        llm_client=llm,
        runs_repo_factory=_runs_repo_factory,
        validation_service_factory=_validation_factory,
        pipeline_service_factory=_pipeline_factory,
    )

    # Avoid touching the real database when gathering context
    monkeypatch.setattr(runner, "_gather_context", lambda flow_id: {"schema_def": {}, "flow_summary": None, "active_pipeline": None})

    run_id = asyncio.run(runner.run("flow-1", "thread-1", {"msg": "hello"}, {"publish": True}, run_id="run-123"))

    assert run_id == "run-123"
    assert similarity.calls == [("flow-1", {"msg": "hello"})]
    assert llm.generated and llm.checked
    assert validation_service.requests == [{"stages": [], "meta": "draft"}]
    assert pipeline_service.created == [("flow-1", {"stages": [], "meta": "draft"})]
    assert pipeline_service.published == ["pip-1"]
    # ensure runs repo factory was used for each stage
    assert runs_repo_instances, "RunsRepo factory was not invoked"
    assert any(
        rec[0] == "tick" and rec[2].get("stage") == "hard_validate"
        for repo in runs_repo_instances
        for rec in repo.records
    )
    # sessions should be committed and closed
    assert sessions and all(sess.closed for sess in sessions)
    # Bus should have emitted a finished event
    assert any(evt[1] == "run.finished" for evt in fake_bus.events)
