from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException as FastHTTPException

class AppError(Exception):
    def __init__(self, status: int = 400, code: str = "UNKNOWN", message: str = "", details=None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details or []

async def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status, content={
        "error": {"code": exc.code, "message": exc.message, "details": exc.details}
    })

async def handle_http_error(request: Request, exc: FastHTTPException):
    # Map FastAPI HTTPException to unified error shape
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    code = "HTTP_ERROR"
    return JSONResponse(status_code=exc.status_code, content={
        "error": {"code": code, "message": message, "details": []}
    })

async def handle_generic_error(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={
        "error": {"code": "INTERNAL", "message": str(exc), "details": []}
    })
