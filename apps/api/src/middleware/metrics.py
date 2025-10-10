from __future__ import annotations


import logging

logger = logging.getLogger(__name__)
import time
from typing import Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..metrics import HTTP_REQUESTS, HTTP_LATENCY


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        method = request.method
        path_label = request.url.path
        try:
            route = request.scope.get("route")
            if route is not None:
                path_label = getattr(route, "path_format", None) or getattr(route, "path", path_label)
        except (AttributeError, TypeError):
            pass
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = getattr(response, "status_code", 200)
            return response
        finally:
            dur = time.perf_counter() - start
            try:
                HTTP_LATENCY.labels(method=method, path=path_label).observe(dur)
                HTTP_REQUESTS.labels(method=method, path=path_label, status=str(status_code)).inc()
            except (ValueError, TypeError, RuntimeError):
                pass
