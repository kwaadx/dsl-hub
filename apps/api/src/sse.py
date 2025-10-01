import asyncio, json, time
from typing import Dict, List, Any, Tuple
from sse_starlette.sse import EventSourceResponse

class _StreamState:
    __slots__ = ("cursor", "subscribers")
    def __init__(self):
        self.cursor = 0
        self.subscribers: List[asyncio.Queue] = []

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

    async def unsubscribe(self, key: str, q: asyncio.Queue):
        state = await self._get_state(key)
        if q in state.subscribers:
            state.subscribers.remove(q)

bus = SSEBus()

async def sse_response(thread_id: str, ping_interval: int = 15):
    q, _ = await bus.subscribe(thread_id)

    async def gen():
        try:
            # initial keep-alive
            yield {"event": "ping", "data": {"ok": True}}
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=ping_interval)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": {"ok": True}}
                    continue
                yield {"event": item["type"], "id": str(item["cursor"]), "data": item["data"]}
        finally:
            await bus.unsubscribe(thread_id, q)

    async def as_sse(ev):
        # EventSourceResponse supports dict-format events
        return ev

    return EventSourceResponse(gen())
