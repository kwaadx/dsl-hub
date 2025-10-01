from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time
from typing import Dict, Tuple

_CACHE: Dict[Tuple[str, str], Tuple[float, Response]] = {}
_TTL = 300.0

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            key = request.headers.get("Idempotency-Key")
            if key:
                ck = (str(request.url.path), key)
                now = time.time()
                if ck in _CACHE:
                    ts, resp = _CACHE[ck]
                    if now - ts < _TTL:
                        return Response(content=resp.body, media_type=resp.media_type, status_code=resp.status_code, headers=dict(resp.headers))
                resp = await call_next(request)
                _CACHE[ck] = (now, resp)
                return resp
        return await call_next(request)
