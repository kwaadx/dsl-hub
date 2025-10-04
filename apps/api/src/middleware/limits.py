from __future__ import annotations

from typing import Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .error import AppError
from ..config import settings


class SizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Reject over-sized JSON payloads early using Content-Length when available.
    This is a best-effort guard; if Content-Length is absent, the request passes through.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        method = request.method.upper()
        if method in {"POST", "PUT", "PATCH"}:
            cl = request.headers.get("content-length")
            if cl:
                try:
                    size = int(cl)
                except ValueError:
                    size = None
                if size is not None and size > int(getattr(settings, "MAX_JSON_SIZE", 1048576)):
                    raise AppError(status=413, code="PAYLOAD_TOO_LARGE",
                                   message=f"Request body too large: {size} > {settings.MAX_JSON_SIZE}")
        return await call_next(request)
