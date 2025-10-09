from fastapi.testclient import TestClient

from ..main import app
from ..routers import messages as messages_router


class _FakeCounter:
    def __init__(self):
        self.calls = []  # list of tuples (action, labels, n)

    def labels(self, role, source):  # noqa: D401
        labels = {"role": role, "source": source}

        class _L:
            def __init__(self, parent, labels):
                self._p = parent
                self._labels = labels

            def inc(self, n: int = 1):  # noqa: D401
                self._p.calls.append(("inc", self._labels, n))

        return _L(self, labels)


class _StubThread:
    def __init__(self, id_: str, flow_id: str = "flow-1"):
        self.id = id_
        self.flow_id = flow_id


class _FakeSession:
    def __init__(self):
        self._thread = _StubThread("t-metrics")
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


def test_post_messages_increments_messages_created_counter(monkeypatch):
    # Patch SessionLocal to avoid real DB
    fake_session = _FakeSession()
    monkeypatch.setattr(messages_router, "SessionLocal", lambda: fake_session, raising=False)

    # Patch metrics counter
    fc = _FakeCounter()
    monkeypatch.setattr(messages_router, "MESSAGES_CREATED", fc, raising=False)

    client = TestClient(app)
    body = {"role": "user", "format": "text", "content": {"text": "Hello"}}
    r = client.post("/threads/t-metrics/messages", json=body)

    assert r.status_code == 201

    # Expect one increment with role=user, source=route
    assert any(
        call[0] == "inc" and call[1].get("role") == "user" and call[1].get("source") == "route"
        for call in fc.calls
    ), f"Unexpected metric calls: {fc.calls}"
