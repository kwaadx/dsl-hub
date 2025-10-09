from fastapi.testclient import TestClient

from apps.api.src.main import app
import apps.api.src.routers.messages as messages_router
from apps.api.src.config import settings


class _StubThread:
    def __init__(self, id_: str, flow_id: str = "flow-1"):
        self.id = id_
        self.flow_id = flow_id


class _FakeSession:
    def __init__(self):
        self._thread = _StubThread("t-rate")
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


def test_rate_limit_per_thread(monkeypatch):
    # Patch SessionLocal used inside the router
    monkeypatch.setattr(messages_router, "SessionLocal", lambda: _FakeSession(), raising=False)
    # Set very low limit
    monkeypatch.setattr(settings, "MESSAGES_RATE_PER_MINUTE", 1, raising=False)

    client = TestClient(app)
    url = "/threads/t-rate/messages?run=0"
    body = {"role": "user", "format": "text", "content": {"text": "Hello"}}

    r1 = client.post(url, json=body)
    assert r1.status_code == 201

    r2 = client.post(url, json=body)
    assert r2.status_code == 429
    data = r2.json()
    assert data.get("error", {}).get("status") == 429


def test_message_text_max_len(monkeypatch):
    # Patch SessionLocal used inside the router
    monkeypatch.setattr(messages_router, "SessionLocal", lambda: _FakeSession(), raising=False)
    # Set max length to 5
    monkeypatch.setattr(settings, "MESSAGE_TEXT_MAX_LEN", 5, raising=False)

    client = TestClient(app)
    url = "/threads/t-rate/messages?run=0"
    body = {"role": "user", "format": "text", "content": {"text": "0123456789"}}

    r = client.post(url, json=body)
    assert r.status_code == 413
    data = r.json()
    assert data.get("error", {}).get("status") == 413
