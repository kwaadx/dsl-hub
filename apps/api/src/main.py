from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import flows, threads, pipelines, summaries, schemas, agent
from .middleware.idempotency import IdempotencyMiddleware
from .middleware.limits import SizeLimitMiddleware
from .middleware.metrics import MetricsMiddleware
from .middleware.auth import AuthMiddleware
from .middleware.error import AppError, handle_app_error, handle_http_error, handle_generic_error
from fastapi import HTTPException as FastHTTPException
from .config import settings
from .routers.system import router as system_router

# Optional routers imported lazily to avoid circulars
from .routers import upgrades

app = FastAPI(
    title="DSL Hub Backend",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middlewares
# CORS comes first so that preflight requests are handled early
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "Accept", "X-Requested-With", "Last-Event-ID"],
)
app.add_middleware(AuthMiddleware)
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(SizeLimitMiddleware)
app.add_middleware(MetricsMiddleware)

# Error handlers (unified error shape)
app.add_exception_handler(AppError, handle_app_error)
app.add_exception_handler(FastHTTPException, handle_http_error)
app.add_exception_handler(Exception, handle_generic_error)

# Routers
app.include_router(system_router)
app.include_router(flows.router)
app.include_router(threads.router)
app.include_router(pipelines.router)
app.include_router(summaries.router)
app.include_router(schemas.router)
app.include_router(agent.router)
app.include_router(upgrades.router)

# Startup init
@app.on_event("startup")
def _init_schema_on_start():
    if settings.INIT_SCHEMA_ON_START:
        try:
            from .schemas.init import main as schema_init_main
            schema_init_main()
        except Exception as e:
            print(f"[startup] schema init failed: {e}")
