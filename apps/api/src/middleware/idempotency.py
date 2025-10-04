from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message
import time, hashlib
from typing import Dict, Tuple, Any, List

from .error import AppError
from ..config import settings

# Cache structure: (method, path, idempotency_key) -> (ts, body_hash_hex, status_code, headers, content_bytes, media_type)
_CACHE: Dict[Tuple[str, str, str], Tuple[float, str, int, Dict[str, str], bytes, str]] = {}

try:
    # Optional metric; if Prometheus not configured, ignore
    from ..metrics import IDEMPOTENCY_CACHE_ENTRIES  # type: ignore
except Exception:  # pragma: no cover
    IDEMPOTENCY_CACHE_ENTRIES = None  # type: ignore


def _sha256_hex(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _sweep_cache(ttl: float, max_entries: int) -> None:
    now = time.time()
    # remove expired
    expired: List[Tuple[str, str, str]] = []
    for k, v in list(_CACHE.items()):
        ts = v[0]
        if now - ts >= ttl:
            expired.append(k)
    for k in expired:
        _CACHE.pop(k, None)
    # enforce size cap
    if max_entries > 0 and len(_CACHE) > max_entries:
        # sort by ts ascending (oldest first)
        items = sorted(_CACHE.items(), key=lambda it: it[1][0])
        to_remove = len(_CACHE) - max_entries
        for k, _ in items[:to_remove]:
            _CACHE.pop(k, None)
    # update gauge
    try:
        if IDEMPOTENCY_CACHE_ENTRIES is not None:
            IDEMPOTENCY_CACHE_ENTRIES.set(len(_CACHE))
    except Exception:
        pass


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
                    return {"type": "http.request", "body": body, "more_body": False}

                # Rebuild request with restored body
                request = Request(request.scope, receive)

                ck = (method, str(request.url.path), key)
                now = time.time()
                ttl = float(getattr(settings, "IDEMPOTENCY_TTL_SEC", 300))
                max_entries = int(getattr(settings, "IDEMPOTENCY_CACHE_MAX", 1000))
                _sweep_cache(ttl, max_entries)
                cached = _CACHE.get(ck)
                if cached:
                    ts, cached_hash, status_code, headers, content, media_type = cached
                    if now - ts < ttl:
                        if cached_hash != body_hash:
                            # Same key reused for different payload within TTL → conflict
                            raise AppError(status=409, code="IDEMPOTENCY_KEY_REUSED",
                                           message="Idempotency-Key has already been used with a different request body",
                                           details=[{"path": request.url.path}])
                        return Response(content=content, media_type=media_type, status_code=status_code, headers=headers)
                # Not cached or expired → process and cache
                resp = await call_next(request)
                # Attempt to read response body bytes (works for standard JSONResponse)
                content_bytes: bytes = b""
                try:
                    content_bytes = resp.body if isinstance(resp.body, (bytes, bytearray)) else bytes(resp.body or b"")
                except Exception:
                    # Fall back: do not cache if body can't be read
                    return resp
                headers = {k.decode() if isinstance(k, bytes) else k: (v.decode() if isinstance(v, bytes) else v)
                           for k, v in resp.headers.items()}
                media_type = resp.media_type or "application/json"
                _CACHE[ck] = (now, body_hash, resp.status_code, headers, content_bytes, media_type)
                _sweep_cache(ttl, max_entries)
                return resp
        return await call_next(request)
