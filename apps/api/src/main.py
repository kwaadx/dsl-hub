from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from .tracing import init_tracer
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from fastapi import HTTPException as FastHTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from .config import settings
from .database import engine, Base
from .middleware.idempotency import IdempotencyMiddleware
from .middleware.limits import SizeLimitMiddleware
from .middleware.metrics import MetricsMiddleware
from .middleware.auth import AuthMiddleware
from .middleware.error import AppError, handle_app_error, handle_generic_error, handle_integrity_error, handle_validation_error
from .routers import flows, threads, pipelines, summaries, schemas, agent, messages, upgrades, system, admin_prompts, admin_compat, agent_logs, schema_store
from .sse import router as sse_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

def create_app() -> FastAPI:
    init_tracer("dslhub-api")

    app = FastAPI(title="DSL Hub Backend", version=settings.APP_VERSION, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SizeLimitMiddleware, max_bytes=settings.API_MAX_JSON_SIZE)
    app.add_middleware(IdempotencyMiddleware, ttl_seconds=settings.API_IDEMPOTENCY_TTL_SEC, max_entries=settings.API_IDEMPOTENCY_CACHE_MAX)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(AuthMiddleware, token_env="API_AUTH_TOKEN")
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(FastHTTPException, handle_generic_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(IntegrityError, handle_integrity_error)
    app.include_router(system.router)
    app.include_router(flows.router)
    app.include_router(threads.router)
    app.include_router(pipelines.router)
    app.include_router(summaries.router)
    app.include_router(schemas.router)
    app.include_router(agent.router)
    app.include_router(messages.router)
    app.include_router(upgrades.router)
    app.include_router(sse_router)
    app.include_router(admin_prompts.router)
    app.include_router(admin_compat.router)
    app.include_router(agent_logs.router)
    app.include_router(schema_store.router)

    @app.get("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
    @app.get("/health")
    def health():
        return {"status": "ok"}
    @app.get("/version")
    def version():
        return {"version": settings.APP_VERSION}
    return app

app = create_app()