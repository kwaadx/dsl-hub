from fastapi import FastAPI
from fastapi.responses import Response
from .routers import flows, threads, pipelines, summaries, schemas, agent
from .middleware.idempotency import IdempotencyMiddleware
from .middleware.limits import SizeLimitMiddleware
from .middleware.metrics import MetricsMiddleware
from .middleware.error import AppError, handle_app_error, handle_http_error, handle_generic_error
from fastapi import HTTPException as FastHTTPException
from .config import settings
from .metrics import prometheus_body

# Optional routers imported lazily to avoid circulars
from .routers import upgrades

app = FastAPI(title="DSL Hub Backend", version=settings.APP_VERSION)

# Middlewares
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(SizeLimitMiddleware)
app.add_middleware(MetricsMiddleware)

# Error handlers (unified error shape)
app.add_exception_handler(AppError, handle_app_error)
app.add_exception_handler(FastHTTPException, handle_http_error)
app.add_exception_handler(Exception, handle_generic_error)

@app.get("/healthz")
def healthz():
    return {"status":"ok"}


@app.get("/version")
def version():
    return {"app":"dsl-hub","version": settings.APP_VERSION}

@app.get("/metrics")
def metrics():
    body, ctype = prometheus_body()
    return Response(content=body, media_type=ctype)

# Routers
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
