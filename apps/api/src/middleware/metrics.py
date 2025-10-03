from __future__ import annotations

import time
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..metrics import HTTP_REQUESTS, HTTP_LATENCY


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:  # type: ignore[override]
        method = request.method
        # Use the raw path without query to keep cardinality low
        path = request.url.path
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = getattr(response, "status_code", 200)
            return response
        finally:
            dur = time.perf_counter() - start
            try:
                HTTP_LATENCY.labels(method=method, path=path).observe(dur)
                HTTP_REQUESTS.labels(method=method, path=path, status=str(status_code)).inc()
            except Exception:
                # Never break request flow due to metrics errors
                pass
