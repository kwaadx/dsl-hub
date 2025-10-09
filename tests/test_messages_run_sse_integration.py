import asyncio
from fastapi.testclient import TestClient

from apps.api.src.main import app
from apps.api.src.sse import bus
import apps.api.src.routers.messages as messages_router


class _FakeRunner:
    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.called = []

    async def run(self, flow_id: str, thread_id: str, user_message, options, run_id: str | None = None):  # noqa: ANN001
        self.called.append((flow_id, thread_id, user_message, options, run_id))
        # Emit minimal lifecycle to simulate FSM
        await bus.publish(thread_id, "run.started", {"run_id": run_id or "r-1", "stage": "discovery"})
        await bus.publish(thread_id, "run.finished", {"run_id": run_id or "r-1", "status": "succeeded"})
        return run_id or "r-1"


class _StubThread:
    def __init__(self, id_: str, flow_id: str = "flow-1"):
        self.id = id_
        self.flow_id = flow_id


class _FakeSession:
    def __init__(self):
        self._thread = _StubThread("t-run")
        self._messages = {}

    def get(self, model, key):  # noqa: ANN001
        if model.__name__ == "Thread":  # type: ignore[attr-defined]
            return self._thread
        if model.__name__ == "Message":  # type: ignore[attr-defined]
            return self._messages.get(str(key))
        return None

    def add(self, m):  # noqa: ANN001
        if m.__class__.__name__ == "Message":
            from datetime import datetime, timezone
            if getattr(m, "created_at", None) is None:
                setattr(m, "created_at", datetime.now(timezone.utc))
            self._messages[str(getattr(m, "id", ""))] = m

    def flush(self):
        pass

    def refresh(self, _m):  # noqa: ANN001
        pass

    def commit(self):
        pass

    def close(self):
        pass


async def _replay_types(thread_id: str):
    items = await bus.replay(thread_id, 0)
    return [it.get("type") for it in (items or [])]


def test_post_messages_run_emits_message_created_and_runner_events(monkeypatch):
    thread_id = "t-run"

    # Monkeypatch SessionLocal to our fake
    fake_session = _FakeSession()
    monkeypatch.setattr(messages_router, "SessionLocal", lambda: fake_session, raising=False)

    # Monkeypatch flow inference to bypass DB
    async def _infer_flow(_tid: str) -> str:
        return "flow-1"

    monkeypatch.setattr(messages_router, "_infer_flow", _infer_flow, raising=False)

    # Inject fake runner via dependency override
    runner = _FakeRunner(thread_id)
    app.dependency_overrides[messages_router.get_agent_runner] = lambda: runner

    # Ensure background task runs immediately by overriding create_task
    def _immediate_task(coro):  # noqa: ANN001
        return asyncio.get_event_loop().run_until_complete(coro)

    monkeypatch.setattr(messages_router.asyncio, "create_task", _immediate_task, raising=False)

    try:
        client = TestClient(app)
        body = {"role": "user", "format": "text", "content": {"text": "Hi"}}
        r = client.post(f"/threads/{thread_id}/messages?run=1", json=body)
        assert r.status_code == 201

        # Validate SSE bus contains expected event types
        types = asyncio.get_event_loop().run_until_complete(_replay_types(thread_id))
        assert "message.created" in types, "Route should emit message.created for user message"
        assert "run.started" in types and "run.finished" in types, "Runner should emit lifecycle events"
    finally:
        app.dependency_overrides.pop(messages_router.get_agent_runner, None)
