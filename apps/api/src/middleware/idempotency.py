from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from dataclasses import dataclass
from typing import Dict, Tuple, List
import time
import hashlib

from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message

from .error import AppError, handle_app_error
from ..config import settings

CacheKey = Tuple[str, str, str]


@dataclass
class CachedResponse:
    timestamp: float
    body_hash: str
    status_code: int
    headers: Dict[str, str]
    content: bytes
    media_type: str


_CACHE: Dict[CacheKey, CachedResponse] = {}

try:
    # Optional metric; if Prometheus not configured, ignore
    from ..metrics import IDEMPOTENCY_CACHE_ENTRIES  # type: ignore
except ImportError:  # pragma: no cover
    IDEMPOTENCY_CACHE_ENTRIES = None  # type: ignore


def _sha256_hex(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _sweep_cache(ttl: float, max_entries: int) -> None:
    now = time.time()
    # remove expired
    expired: List[CacheKey] = []
    for k, v in list(_CACHE.items()):
        if now - v.timestamp >= ttl:
            expired.append(k)
    for k in expired:
        _CACHE.pop(k, None)
    # enforce size cap
    if 0 < max_entries < len(_CACHE):
        # sort by ts ascending (oldest first)
        items = sorted(_CACHE.items(), key=lambda it: it[1].timestamp)
        to_remove = len(_CACHE) - max_entries
        for k, _ in items[:to_remove]:
            _CACHE.pop(k, None)
    # update gauge
    try:
        if IDEMPOTENCY_CACHE_ENTRIES is not None:
            IDEMPOTENCY_CACHE_ENTRIES.set(len(_CACHE))
    except (ValueError, TypeError, RuntimeError):
        pass


def _serialize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    serialized: Dict[str, str] = {}
    for key, value in headers.items():
        if not isinstance(key, str):
            key = key.decode()
        if not isinstance(value, str):
            value = value.decode()
        serialized[key] = value
    return serialized


def _build_response(entry: CachedResponse) -> Response:
    headers = {k: v for k, v in entry.headers.items() if k.lower() != "content-length"}
    return Response(content=entry.content, media_type=entry.media_type, status_code=entry.status_code, headers=headers)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        if method == "POST":
            key = request.headers.get("Idempotency-Key")
            if key:
                # Read body safely and restore the stream
                body = await request.body()
                body_hash = _sha256_hex(body)

                async def receive() -> Message:
                    return dict(type="http.request", body=body, more_body=False)

                # Rebuild request with restored body
                request = Request(request.scope, receive)

                ck: CacheKey = (method, str(request.url.path), key)
                now = time.time()
                ttl = float(getattr(settings, "IDEMPOTENCY_TTL_SEC", 300))
                max_entries = int(getattr(settings, "IDEMPOTENCY_CACHE_MAX", 1000))
                _sweep_cache(ttl, max_entries)
                cached = _CACHE.get(ck)
                if cached:
                    if now - cached.timestamp < ttl:
                        if cached.body_hash != body_hash:
                            error = AppError(
                                status=409,
                                code="IDEMPOTENCY_KEY_REUSED",
                                message="Idempotency-Key has already been used with a different request body",
                                details=[{"path": request.url.path}],
                            )
                            return await handle_app_error(request, error)
                        return _build_response(cached)
                # Not cached or expired → process and cache
                resp = await call_next(request)
                try:
                    content_chunks = [chunk async for chunk in resp.body_iterator]
                except Exception:
                    return resp
                content_bytes = b"".join(content_chunks)
                media_type = resp.media_type or resp.headers.get("content-type", "application/json")
                headers = _serialize_headers(dict(resp.headers.items()))
                entry = CachedResponse(
                    timestamp=now,
                    body_hash=body_hash,
                    status_code=resp.status_code,
                    headers=headers,
                    content=content_bytes,
                    media_type=media_type,
                )
                _CACHE[ck] = entry
                _sweep_cache(ttl, max_entries)
                response = _build_response(entry)
                if resp.background:
                    response.background = resp.background
                return response
        return await call_next(request)
