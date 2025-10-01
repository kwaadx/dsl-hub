from fastapi import FastAPI
from .routers import flows, threads, pipelines, summaries, schemas, agent
from .middleware.idempotency import IdempotencyMiddleware
from .middleware.error import AppError, handle_app_error, handle_http_error, handle_generic_error
from fastapi import HTTPException as FastHTTPException

# Optional routers imported lazily to avoid circulars
from .routers import upgrades

app = FastAPI(title="DSL Hub Backend", version="0.1.0")

# Middlewares
app.add_middleware(IdempotencyMiddleware)

# Error handlers (unified error shape)
app.add_exception_handler(AppError, handle_app_error)
app.add_exception_handler(FastHTTPException, handle_http_error)
app.add_exception_handler(Exception, handle_generic_error)

@app.get("/healthz")
def healthz():
    return {"status":"ok"}

@app.get("/version")
def version():
    return {"app":"dsl-hub","version":"0.1.0"}

# Routers
app.include_router(flows.router)
app.include_router(threads.router)
app.include_router(pipelines.router)
app.include_router(summaries.router)
app.include_router(schemas.router)
app.include_router(agent.router)
app.include_router(upgrades.router)
