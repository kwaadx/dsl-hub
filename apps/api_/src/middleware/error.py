from fastapi import Request, status
from fastapi.responses import JSONResponse
from ..config.logger import logger

async def error_handler(request: Request, exc: Exception):
    """
    Global exception handler for the application.
    """
    status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    message = str(exc) or "Internal Server Error"

    logger.error(f"Error: {message}")

    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "status": status_code}}
    )

class HTTPException(Exception):
    """
    Custom HTTP exception that can be raised from anywhere in the application.
    """
    def __init__(self, status_code: int, message: str = None):
        self.status_code = status_code
        self.message = message
        super().__init__(message)
