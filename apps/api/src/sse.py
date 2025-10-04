import asyncio, time
from typing import Dict, List, Any, Tuple
from sse_starlette.sse import EventSourceResponse

from collections import deque
from .metrics import SSE_EVENTS, SSE_CONNECTIONS, SSE_SESSION_SECONDS
from .config import settings

class _StreamState:
    __slots__ = ("cursor", "subscribers", "buffer")
    def __init__(self):
        self.cursor = 0
        self.subscribers: List[asyncio.Queue] = []
        try:
            maxlen = int(getattr(settings, "SSE_BUFFER_MAXLEN", 500))
        except (ValueError, TypeError):
            maxlen = 500
        self.buffer = deque(maxlen=maxlen)

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
        # prune by TTL to avoid unbounded growth
        try:
            ttl_ms = int(getattr(settings, "SSE_BUFFER_TTL_SEC", 300)) * 1000
        except (ValueError, TypeError):
            ttl_ms = 300 * 1000
        now_ms = int(time.time() * 1000)
        while state.buffer and (now_ms - state.buffer[0]["ts"]) > ttl_ms:
            try:
                state.buffer.popleft()
            except IndexError:
                break
        for q in list(state.subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                # Drop the oldest if full; minimal backpressure strategy
                try:
                    _ = q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                q.put_nowait(payload)
        try:
            SSE_EVENTS.labels(event=event_type).inc()
        except ValueError:
            pass
        return state.cursor

    async def subscribe(self, key: str) -> Tuple[asyncio.Queue, int]:
        state = await self._get_state(key)
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        state.subscribers.append(q)
        try:
            SSE_CONNECTIONS.labels(action="open").inc()
        except ValueError:
            pass
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
        try:
            SSE_CONNECTIONS.labels(action="close").inc()
        except ValueError:
            pass

bus = SSEBus()


def _to_sse_message(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize internal bus item to SSE message payload.
    Keeps runtime behavior identical while removing duplication.
    """
    data = item["data"]
    ts = item["ts"]
    if isinstance(data, dict):
        payload = {**data, "ts": ts}
    else:
        payload = {"value": data, "ts": ts}
    return dict(event=item["type"], id=str(item["cursor"]), data=payload)

async def sse_response(thread_id: str, ping_interval: int = 15, last_event_id: str | None = None):
    # subscribe first
    q, _ = await bus.subscribe(thread_id)
    # parse last_event_id for replay
    since = None
    if last_event_id:
        try:
            since = int(last_event_id)
        except ValueError:
            since = None

    async def gen():
        started = time.time()
        try:
            # initial replay if possible
            if since is not None:
                replay = await bus.replay(thread_id, since)
                if replay:
                    for item in replay:
                        yield _to_sse_message(item)
            # initial keep-alive
            yield {"event": "ping", "data": ""}
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=ping_interval)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
                    continue
                yield _to_sse_message(item)
        finally:
            try:
                dur = max(0.0, time.time() - started)
                SSE_SESSION_SECONDS.observe(dur)
            except ValueError:
                pass
            await bus.unsubscribe(thread_id, q)

    return EventSourceResponse(gen())
