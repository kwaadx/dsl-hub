from fastapi.testclient import TestClient
from typing import Any, Dict
from datetime import datetime, timezone

from ..main import app
from ..routers import messages as messages_router


class _StubThread:
    def __init__(self, id_: str, flow_id: str = "flow-1"):
        self.id = id_
        self.flow_id = flow_id


class _FakeSession:
    """Minimal fake SessionLocal for messages router to avoid real DB.
    Supports get/add/flush/refresh/commit/close.
    Stores messages in-memory.
    """

    def __init__(self, has_thread: bool = True):
        self._has_thread = has_thread
        self._messages: Dict[str, Any] = {}
        self._commits = 0
        self.closed = False

    # Expose a predictable created_at for tests
    def _now(self):
        return datetime.now(timezone.utc)

    def get(self, model, key):  # noqa: ANN001
        if model.__name__ == "Thread":  # type: ignore[attr-defined]
            if self._has_thread:
                return _StubThread(str(key))
            return None
        if model.__name__ == "Message":  # type: ignore[attr-defined]
            return self._messages.get(str(key))
        return None

    def add(self, m):  # noqa: ANN001
        # Mimic SQLAlchemy model with attributes used by the router
        if m.__class__.__name__ == "Message":
            # Attach created_at if missing
            if getattr(m, "created_at", None) is None:
                setattr(m, "created_at", self._now())
            self._messages[str(getattr(m, "id", ""))] = m

    def flush(self):
        return None

    def refresh(self, _m):  # noqa: ANN001
        # Nothing to load additionally in fake
        return None

    def commit(self):
        self._commits += 1

    def execute(self, _q):  # noqa: ANN001
        class _Res:
            def __init__(self, rows):
                self._rows = rows

            def scalars(self):
                class _Scalars:
                    def __init__(self, rows):
                        self._rows = rows

                    def all(self):
                        return list(self._rows)

                return _Scalars(self._rows)

        # For simplicity, return messages sorted by created_at
        rows = sorted(self._messages.values(), key=lambda x: (getattr(x, "created_at", self._now()), getattr(x, "id", "")))
        return _Res(rows)

    def close(self):
        self.closed = True


def test_post_messages_is_idempotent(monkeypatch):
    # Patch SessionLocal used inside the router to our fake
    fake_session = _FakeSession(has_thread=True)
    monkeypatch.setattr(messages_router, "SessionLocal", lambda: fake_session, raising=False)

    client = TestClient(app)

    body = {"role": "user", "format": "text", "content": {"text": "Hello"}}
    idem = "fixed-idem-key-1"
    url = "/threads/t-1/messages?run=0"

    r1 = client.post(url, json=body, headers={"Idempotency-Key": idem})
    r2 = client.post(url, json=body, headers={"Idempotency-Key": idem})

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json() == r2.json(), "Idempotent POST must return identical cached response on retry"


def test_get_messages_404_when_thread_missing(monkeypatch):
    # Session without thread present
    fake_session = _FakeSession(has_thread=False)
    monkeypatch.setattr(messages_router, "SessionLocal", lambda: fake_session, raising=False)

    client = TestClient(app)
    r = client.get("/threads/t-missing/messages")
    assert r.status_code == 404
    data = r.json()
    # unified error handler shape
    assert data.get("error", {}).get("status") == 404
