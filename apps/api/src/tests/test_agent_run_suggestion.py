from fastapi.testclient import TestClient

from ..main import app
from ..routers import agent as agent_router
from ..agent.graph import AgentRunner


def test_agent_run_returns_suggestion(monkeypatch):
    # Monkeypatch flow inference to bypass DB
    async def _infer_flow(thread_id: str) -> str:
        return "flow-1"

    monkeypatch.setattr(agent_router, "_infer_flow", _infer_flow, raising=False)
    # Prepare fake dependencies
    cand = {"pipeline_id": "pip-99", "version": "1.0.0", "score": 1.0}

    class _FakeSim:
        def __init__(self):
            self.calls = []

        def find_candidate(self, flow_id, user_message):
            self.calls.append((flow_id, user_message))
            return cand

    class _FakeSession:
        def __init__(self):
            self.commits = 0
            self.closed = 0

        def commit(self):
            self.commits += 1

        def close(self):
            self.closed += 1

    class _FakeRunsRepo:
        def __init__(self):
            self.actions = []

        def start(self, *args, **kwargs):
            self.actions.append(("start", args, kwargs))

        def tick(self, *args, **kwargs):
            self.actions.append(("tick", args, kwargs))

        def finish(self, *args, **kwargs):
            self.actions.append(("finish", args, kwargs))

        def add_issues(self, *args, **kwargs):  # pragma: no cover - not used but keeps protocol happy
            self.actions.append(("add_issues", args, kwargs))

    fake_similarity = _FakeSim()
    sessions: list[_FakeSession] = []
    repos: list[_FakeRunsRepo] = []

    def _session_factory():
        s = _FakeSession()
        sessions.append(s)
        return s

    def _runs_repo_factory(session):
        repo = _FakeRunsRepo()
        repos.append(repo)
        return repo

    fake_runner = AgentRunner(
        session_factory=_session_factory,
        similarity_service=fake_similarity,
        runs_repo_factory=_runs_repo_factory,
    )

    app.dependency_overrides[agent_router.get_agent_runner] = lambda: fake_runner
    try:
        client = TestClient(app)
        r = client.post("/threads/abc/agent/run", json={"user_message": {"hello": "world"}, "options": {}})
    finally:
        app.dependency_overrides.pop(agent_router.get_agent_runner, None)

    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert data["suggestion"] == cand
    # Ensure fake dependencies were used
    assert fake_similarity.calls == [("flow-1", {"hello": "world"})]
    assert sessions and sessions[0].commits == 1
    assert repos and any(action[0] == "finish" for action in repos[0].actions)
