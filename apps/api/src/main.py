from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
from config.env import env
from config.logger import logger
from .middleware.error import error_handler, HTTPException
from .routes import router as api_router
from .health.routes import router as health_router

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=env.CORS_ORIGIN.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0]
        else:
            client_ip = request.client.host

        # Log request
        logger.info(f"{request.method} {request.url.path} - Client: {client_ip}")

        # Process request
        response = await call_next(request)

        # Log response time
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s")

        return response

app.add_middleware(LoggingMiddleware)

# Add exception handlers
app.add_exception_handler(Exception, error_handler)
app.add_exception_handler(HTTPException, error_handler)

# Add routes
app.include_router(health_router, prefix="/health")
app.include_router(api_router, prefix="/api")

# Export app
__all__ = ["app"]
