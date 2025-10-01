# DSL Hub Backend (FastAPI + LangGraph + SSE)

This repository is a production-ready MVP skeleton that implements:
- FastAPI app
- SSE stream per thread
- LangGraph-based agent FSM (real graph: init → search_existing → (decide) → generate → self_check → hard_validate → persist → [optional publish] → finish)
- Repositories/Services layer
- Routers for flows, threads, messages, agent, pipelines, summaries, schemas
- Pydantic DTOs
- Postgres via SQLAlchemy 2.x (sync engine)

> NOTE: This is a **skeleton** with working endpoints and mocked LLM. 
> You should plug your real SQLAlchemy models and Alembic migrations. 
> The file `app/models.py` contains your provided models (slightly adjusted imports for Base).

## Quickstart

1) Create `.env` from example:
```
cp .env.example .env
```

2) Install dependencies:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3) Run (you must have a Postgres DB available and alembic upgraded):
```
uvicorn app.main:app --reload
```

4) Open `GET /healthz` to check health. Connect your frontend to the routes described in the docs.

## Env Vars

See `.env.example`. Important ones:
- `DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/dslhub`
- `APP_SCHEMA_CHANNEL=stable`
- `SIMILARITY_THRESHOLD=0.75`
- `SSE_PING_INTERVAL=15`

## Project layout

```
app/
  main.py                - FastAPI app factory; router registration
  config.py              - settings (Pydantic Settings)
  database.py            - engine + SessionLocal + Base
  models.py              - SQLAlchemy models (from your spec)
  sse.py                 - in-memory SSE bus (per thread) + helpers
  dto.py                 - Pydantic request/response schemas
  repositories/          - DB accessors (FlowRepo, ThreadRepo, …)
  services/              - FlowService, ThreadService, PipelineService, ValidationService, SimilarityService
  agent/graph.py         - LangGraph FSM + AgentRunner adapter
  routers/
    flows.py             - /flows
    threads.py           - /flows/{id}/threads, /threads/*
    messages.py          - /threads/{id}/messages
    agent.py             - /threads/{id}/events (SSE), /threads/{id}/agent/run
    pipelines.py         - /flows/{id}/pipelines, /pipelines/*
    summaries.py         - /flows/{id}/summary/active, /threads/{id}/summaries
    schemas.py           - /schema/channels, ...
```

## Notes

- SSE is **in-memory**; for multi-worker deployments replace it with Postgres LISTEN/NOTIFY or Redis.
- LLM is mocked; replace `services/llm.py` with a real provider and adjust `agent/graph.py`.
- JSON Schema hard validation uses `jsonschema`. Place your DSL json schema in DB `schema_def.json`.
