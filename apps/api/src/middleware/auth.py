from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable, Awaitable

from .error import AppError
from ..config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Minimal Bearer token auth for mutating requests.
    Enabled only if settings.AUTH_TOKEN is set (non-empty).
    Applies to methods: POST, PUT, PATCH, DELETE.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        token = getattr(settings, "AUTH_TOKEN", None)
        method = request.method.upper()
        if token and method in {"POST", "PUT", "PATCH", "DELETE"}:
            auth = request.headers.get("Authorization")
            expected = f"Bearer {token}"
            if auth != expected:
                raise AppError(status=401, code="UNAUTHORIZED", message="Missing or invalid Authorization token")
        return await call_next(request)
