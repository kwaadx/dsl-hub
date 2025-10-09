from fastapi.testclient import TestClient
import asyncio

from ..main import app
from ..sse import bus


def test_sse_events_returns_204_when_replay_not_possible():
    client = TestClient(app)
    # No events were published under this key; providing Last-Event-ID should yield 204
    r = client.get("/threads/t-no-buffer/events", headers={"Last-Event-ID": "1"})
    assert r.status_code == 204


def test_sse_events_returns_200_with_event_stream_when_replay_possible():
    client = TestClient(app)
    key = "t-has-buffer"

    # Publish at least one event so that replay from 0 is possible
    asyncio.get_event_loop().run_until_complete(bus.publish(key, "test.event", {"ok": True}))

    r = client.get(f"/threads/{key}/events", headers={"Last-Event-ID": "0"})
    assert r.status_code == 200
    ctype = r.headers.get("content-type", "")
    assert "text/event-stream" in ctype
