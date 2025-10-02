from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException as FastHTTPException
from starlette.responses import Response
from typing import Any, List, Optional


class AppError(Exception):
    def __init__(self, status: int = 400, code: str = "UNKNOWN", message: str = "",
                 details: Optional[List[Any]] = None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details or []


def _error_response(status_code: int, code: str, message: str, details: Optional[List[Any]] = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={
        "error": {"code": code, "message": message, "details": details or []}
    })


async def handle_app_error(request: Request, exc: Exception) -> Response:
    req_info = {"path": str(request.url.path), "method": request.method}
    if isinstance(exc, AppError):
        details = list(exc.details) if isinstance(exc.details, list) else []
        details.append({"request": req_info})
        return _error_response(status_code=exc.status, code=exc.code, message=exc.message, details=details)
    return _error_response(status_code=500, code="INTERNAL", message=str(exc), details=[{"request": req_info}])


async def handle_http_error(request: Request, exc: Exception) -> Response:
    req_info = {"path": str(request.url.path), "method": request.method}
    if isinstance(exc, FastHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        code = "HTTP_ERROR"
        return _error_response(status_code=exc.status_code, code=code, message=message, details=[{"request": req_info}])
    return _error_response(status_code=500, code="INTERNAL", message=str(exc), details=[{"request": req_info}])


async def handle_generic_error(request: Request, exc: Exception) -> Response:
    req_info = {"path": str(request.url.path), "method": request.method}
    return _error_response(status_code=500, code="INTERNAL", message=str(exc), details=[{"request": req_info}])
