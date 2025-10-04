from fastapi.testclient import TestClient

from apps.api.src.main import app
import apps.api.src.routers.agent as agent_router


def test_agent_run_returns_suggestion(monkeypatch):
    # Monkeypatch flow inference to bypass DB
    monkeypatch.setattr(agent_router, "_infer_flow", lambda thread_id: "flow-1", raising=False)
    # Monkeypatch SimilarityService to always find a candidate
    cand = {"pipeline_id": "pip-99", "version": "1.0.0", "score": 1.0}

    class _FakeSim:
        def find_candidate(self, flow_id, user_message):
            return cand

    monkeypatch.setattr(agent_router, "SimilarityService", lambda: _FakeSim(), raising=False)

    client = TestClient(app)
    r = client.post("/threads/abc/agent/run", json={"user_message": {"hello": "world"}, "options": {}})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert data["suggestion"] == cand
