from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException as FastHTTPException
from fastapi.exceptions import RequestValidationError
from starlette.responses import Response
from typing import Any, List, Optional

from sqlalchemy.exc import IntegrityError


class AppError(Exception):
    def __init__(self, status: int = 400, code: str = "UNKNOWN", message: str = "",
                 details: Optional[List[Any]] = None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details or []


def _error_response(status_code: int, code: str, message: str, details: Optional[List[Any]] = None) -> JSONResponse:
    detail_list = list(details) if isinstance(details, list) else []
    content = {
        "code": code,
        "message": message,
        "details": detail_list,
        "error": {"code": code, "message": message, "details": detail_list},
    }
    return JSONResponse(status_code=status_code, content=content)


def _with_request(details: Optional[List[Any]], request: Request) -> List[Any]:
    base = list(details) if isinstance(details, list) else []
    base.append({"request": {"path": str(request.url.path), "method": request.method}})
    return base


async def handle_app_error(request: Request, exc: Exception) -> Response:
    if isinstance(exc, AppError):
        return _error_response(status_code=exc.status, code=exc.code, message=exc.message,
                               details=_with_request(exc.details, request))
    return _error_response(status_code=500, code="INTERNAL", message="Internal server error",
                           details=_with_request([{"reason": str(exc)}], request))


async def handle_http_error(request: Request, exc: Exception) -> Response:
    if isinstance(exc, FastHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        code = "HTTP_ERROR"
        return _error_response(status_code=exc.status_code, code=code, message=message,
                               details=_with_request(None, request))
    return _error_response(status_code=500, code="INTERNAL", message="Internal server error",
                           details=_with_request([{"reason": str(exc)}], request))


async def handle_validation_error(request: Request, exc: Exception) -> Response:
    if isinstance(exc, RequestValidationError):
        details: List[Any] = []
        for err in exc.errors():
            # err: {'loc': ('body','field'), 'msg': '...', 'type': '...'}
            details.append({
                "loc": list(err.get("loc", [])),
                "message": err.get("msg", "validation error"),
                "type": err.get("type", "")
            })
        return _error_response(status_code=422, code="VALIDATION_ERROR", message="Request validation failed",
                               details=_with_request(details, request))
    return _error_response(status_code=500, code="INTERNAL", message="Internal server error",
                           details=_with_request([{"reason": str(exc)}], request))


async def handle_integrity_error(request: Request, exc: Exception) -> Response:
    # Map DB unique constraint violations to a clean, user-friendly error
    if isinstance(exc, IntegrityError):
        # Try to detect unique violation and the field from constraint name
        code = "DUPLICATE"
        status = 409
        field = None
        constraint = None
        reason = None
        try:
            # psycopg2 exposes pgcode and diag
            orig = getattr(exc, "orig", None)
            pgcode = getattr(orig, "pgcode", None)
            if pgcode == "23505":  # unique_violation
                diag = getattr(orig, "diag", None)
                constraint = getattr(diag, "constraint_name", None) if diag else None
        except Exception:
            pass
        # Fallback: parse from string
        msg = str(exc)
        if not constraint and "flow_name_key" in msg:
            constraint = "flow_name_key"
        if not constraint and "flow_slug_key" in msg:
            constraint = "flow_slug_key"
        if constraint == "flow_name_key":
            field = "name"
            message = "Flow name already exists"
        elif constraint == "flow_slug_key":
            field = "slug"
            message = "Flow slug already exists"
        else:
            message = "Duplicate resource"
            reason = msg
        details: List[Any] = []
        if field:
            details.append({"field": field})
        if constraint:
            details.append({"constraint": constraint})
        if reason:
            details.append({"reason": reason})
        return _error_response(status_code=status, code=code, message=message,
                               details=_with_request(details, request))
    # Fallback
    return _error_response(status_code=500, code="INTERNAL", message="Internal server error",
                           details=_with_request([{"reason": str(exc)}], request))


async def handle_generic_error(request: Request, exc: Exception) -> Response:
    return _error_response(status_code=500, code="INTERNAL", message="Internal server error",
                           details=_with_request([{"reason": str(exc)}], request))
