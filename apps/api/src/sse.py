from __future__ import annotations

import asyncio, time, json
from typing import AsyncIterator, Dict, Any, Optional, List
from collections import deque
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter
from .config import settings


class ChannelBus:
    def __init__(self, maxlen: int = None, ttl: int = None):
        self.maxlen = maxlen or settings.API_SSE_BUFFER_MAXLEN
        self.ttl = ttl or settings.API_SSE_BUFFER_TTL_SEC
        self._buf: deque[Dict[str, Any]] = deque(maxlen=self.maxlen)
        self._subs: List[asyncio.Queue] = []
        self._chan_subs: dict[str, list[asyncio.Queue]] = {}
    def publish(self, data: Any, *, channel: str | None = None) -> None:
        item = {"data": data, "ts": time.time(), "channel": channel}
        self._buf.append(item)
        targets = list(self._subs)
        if channel:
            targets += self._chan_subs.get(channel, [])
        for q in list(set(targets)):
            try:
                q.put_nowait(item)
            except asyncio.QueueFull:
                # drop slow subscriber
                for lst in (self._subs, self._chan_subs.get(channel, [])):
                    if q in lst:
                        lst.remove(q)
    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subs.append(q)
        return q
    def subscribe_channel(self, channel: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._chan_subs.setdefault(channel, []).append(q)
        return q
    def replay(self, since_ts: float, channel: str | None = None) -> List[Dict[str, Any]]:
        cutoff = time.time() - self.ttl
        items = [m for m in self._buf if m["ts"] >= max(cutoff, since_ts)]
        if channel:
            items = [m for m in items if m.get("channel") == channel]
        return items

    def __init__(self, maxlen: int = None, ttl: int = None):
        self.maxlen = maxlen or settings.API_SSE_BUFFER_MAXLEN
        self.ttl = ttl or settings.API_SSE_BUFFER_TTL_SEC
        self._buf: deque[Dict[str, Any]] = deque(maxlen=self.maxlen)
        self._subs: List[asyncio.Queue] = []
    def publish(self, data: Any) -> None:
        item = {"data": data, "ts": time.time()}
        self._buf.append(item)
        for q in list(self._subs):
            try:
                q.put_nowait(item)
            except asyncio.QueueFull:
                self._subs.remove(q)
    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subs.append(q)
        return q
    def replay(self, since_ts: float) -> List[Dict[str, Any]]:
        cutoff = time.time() - self.ttl
        return [m for m in self._buf if m["ts"] >= max(cutoff, since_ts)]
bus = ChannelBus()
def _to_sse_message(item: Dict[str, Any]) -> Dict[str, Any]:
    data = item["data"]; ts = item["ts"]
    payload = data if isinstance(data, dict) else {"value": data}
    payload["ts"] = ts
    return {"event": "message", "data": json.dumps(payload), "id": str(ts)}
router = APIRouter(prefix="/sse", tags=["sse"])
@router.get("/stream")
async def stream(last_event_id: Optional[str] = None):
    q = bus.subscribe()
    async def gen() -> AsyncIterator[dict]:
        if last_event_id:
            try:
                since_ts = float(last_event_id)
                for item in bus.replay(since_ts):
                    yield _to_sse_message(item)
            except ValueError:
                pass
        ping_interval = max(5, settings.API_SSE_PING_INTERVAL)
        last_ping = time.time()
        try:
            while True:
                try:
                    item = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield _to_sse_message(item)
                except asyncio.TimeoutError:
                    now = time.time()
                    if now - last_ping >= ping_interval:
                        last_ping = now
                        yield {"event": "ping", "data": "ping"}
        finally:
            try:
                bus._subs.remove(q)
            except ValueError:
                pass
    return EventSourceResponse(gen(), headers={"Cache-Control": "no-cache"})