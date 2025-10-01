from fastapi import FastAPI
from .routers import flows, threads, messages, pipelines, summaries, schemas, agent

app = FastAPI(title="DSL Hub Backend", version="0.1.0")

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
