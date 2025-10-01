import asyncio, json, time
from typing import Dict, List, Any, Tuple
from sse_starlette.sse import EventSourceResponse

from collections import deque

class _StreamState:
    __slots__ = ("cursor", "subscribers", "buffer")
    def __init__(self):
        self.cursor = 0
        self.subscribers: List[asyncio.Queue] = []
        self.buffer = deque(maxlen=500)

class SSEBus:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._streams: Dict[str, _StreamState] = {}

    async def _get_state(self, key: str) -> _StreamState:
        async with self._lock:
            if key not in self._streams:
                self._streams[key] = _StreamState()
            return self._streams[key]

    async def publish(self, key: str, event_type: str, data: Any) -> int:
        state = await self._get_state(key)
        state.cursor += 1
        payload = {
            "type": event_type,
            "data": data,
            "cursor": state.cursor,
            "ts": int(time.time() * 1000),
        }
        # buffer for replay
        state.buffer.append(payload)
        for q in list(state.subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                # Drop oldest if full; minimal backpressure strategy
                try:
                    _ = q.get_nowait()
                except Exception:
                    pass
                q.put_nowait(payload)
        return state.cursor

    async def subscribe(self, key: str) -> Tuple[asyncio.Queue, int]:
        state = await self._get_state(key)
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        state.subscribers.append(q)
        return q, state.cursor

    async def can_replay(self, key: str, since_cursor: int) -> bool:
        state = await self._get_state(key)
        if not state.buffer:
            return False
        earliest = state.buffer[0]["cursor"]
        return since_cursor >= (earliest - 1)

    async def replay(self, key: str, since_cursor: int) -> List[Dict[str, Any]] | None:
        state = await self._get_state(key)
        if not state.buffer:
            return [] if since_cursor == 0 else None
        earliest = state.buffer[0]["cursor"]
        if since_cursor < (earliest - 1):
            return None
        return [e for e in list(state.buffer) if e["cursor"] > since_cursor]

    async def unsubscribe(self, key: str, q: asyncio.Queue):
        state = await self._get_state(key)
        if q in state.subscribers:
            state.subscribers.remove(q)

bus = SSEBus()

async def sse_response(thread_id: str, ping_interval: int = 15, last_event_id: str | None = None):
    # subscribe first
    q, _ = await bus.subscribe(thread_id)
    # parse last_event_id for replay
    since = None
    if last_event_id:
        try:
            since = int(last_event_id)
        except Exception:
            since = None

    async def gen():
        try:
            # initial replay if possible
            if since is not None:
                replay = await bus.replay(thread_id, since)
                if replay:
                    for item in replay:
                        data = item["data"]
                        if isinstance(data, dict):
                            data = {**data, "ts": item["ts"]}
                        else:
                            data = {"value": data, "ts": item["ts"]}
                        yield {"event": item["type"], "id": str(item["cursor"]), "data": data}
            # initial keep-alive
            yield {"event": "ping", "data": {"ok": True}}
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=ping_interval)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": {"ok": True}}
                    continue
                data = item["data"]
                if isinstance(data, dict):
                    data = {**data, "ts": item["ts"]}
                else:
                    data = {"value": data, "ts": item["ts"]}
                yield {"event": item["type"], "id": str(item["cursor"]), "data": data}
        finally:
            await bus.unsubscribe(thread_id, q)

    return EventSourceResponse(gen())
