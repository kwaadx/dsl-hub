# DSL Hub Backend (FastAPI + LangGraph + SSE)

This repository is a production-ready MVP skeleton that implements:
- FastAPI app
- SSE stream per thread
- LangGraph-based agent FSM (real graph: init → search_existing → (decide) → generate → self_check → hard_validate → persist → [optional publish] → finish)
- Repositories/Services layer
- Routers for flows, threads, messages, agent, pipelines, summaries, schemas
- Pydantic DTOs
- Postgres via SQLAlchemy 2.x (sync engine)

> NOTE: This is a **skeleton** with working endpoints and an OpenAI-based LLM (configure API_OPENAI_API_KEY).
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

4) Open `GET /health` to check health. Connect your frontend to the routes described in the docs.

## Env Vars

See `.env.example`. Important ones:
- `DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/dslhub`
- `APP_SCHEMA_CHANNEL=stable`
- `SIMILARITY_THRESHOLD=0.75`
- `SSE_PING_INTERVAL=15`
- `API_MESSAGES_RATE_PER_MINUTE` — per-thread rate limit for POST /threads/{id}/messages over 60s window (default 30; set 0 to disable)
- `API_MESSAGE_TEXT_MAX_LEN` — max length (characters) for text/markdown message content.text (default 4000)

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

## Observability

The API exposes Prometheus metrics at GET /metrics. Useful series:
- http_requests_total{method,path,status}
- http_request_duration_seconds{method,path}
- sse_events_total{event}, sse_connections_total{action}, sse_session_duration_seconds
- agent_runs_total{mode}, agent_run_duration_seconds{status}, agent_run_errors_total
- messages_created_total{role,source}

Alert suggestions:
- agent_run_errors_total > 0 for 5m
- Sudden drop of messages_created_total{role="assistant"}
- Abnormally low sse_session_duration_seconds (indicates reconnect loops)

## Notes

- SSE is **in-memory**; for multi-worker deployments replace it with Postgres LISTEN/NOTIFY or Redis.
- LLM uses OpenAI via `services/llm.py`; adjust `agent/graph.py` only if you change LLM prompting. Ensure `API_OPENAI_API_KEY` is set.
- JSON Schema hard validation uses `jsonschema`. Place your DSL json schema in DB `schema_def.json`.


## Chat endpoints and SSE (Stage 1: Contract)

The following API contract defines the backend source of truth for chat history and standardized SSE events. Stage 1 requires documentation only; code changes follow in Stage 2+.

### Endpoints

- GET /threads/{thread_id}/messages
  - Query: limit=1..200 (default 50), before=<cursor>
  - Returns 200 with an array of messages sorted by created_at ASC.
  - Message fields: id, role, format, content, created_at, parent_id?, tool_name?, tool_result?

- POST /threads/{thread_id}/messages?run=1
  - Creates a user message and (optionally) starts the agent FSM when run=1.
  - Headers: Content-Type: application/json; Authorization (if enabled); Idempotency-Key recommended.
  - Body (MessageIn): { role: "user", format: "text", content: { text: "..." }, parent_id?: "<uuid>" }
  - 201 response: { id, created_at, meta: { run: { run_id, status: "queued" } } }

- POST /threads/{thread_id}/agent/event
  - Accepts UI events; responds 202 and emits ui.ack via SSE.

- POST /threads/{thread_id}/agent/run
  - Legacy path; prefer POST /messages?run=1 going forward.

### SSE events

- message.created { message_id, role, format, content, ts }
- run.started { run_id, stage, ts }
- run.stage { run_id, stage, status, [error], ts }
- suggestion { ... , ts }
- issues { items: [...], ts }
- pipeline.created { pipeline_id, version, status, ts }
- pipeline.published { pipeline_id, version, ts }
- run.finished { run_id, status, [error], ts }
- ui.ack { kind, msg, event, ts }
- ping

SSE reconnection and replay:
- Clients should pass Last-Event-ID on reconnect. If the server cannot replay (buffer expired), it returns 204 No Content; the client should reconnect without Last-Event-ID.


## Feature flag: legacy agent.msg SSE emission (Stage 10)

To maintain backward compatibility during the chat migration, the backend can optionally emit the legacy SSE event `agent.msg` alongside the new `message.created`:

- API_EMIT_LEGACY_AGENT_MSG=true|false (default: true)
  - true: agent FSM emits both message.created and agent.msg (with message_id) for assistant/system outputs.
  - false: only message.created is emitted (recommended after frontend migration).

Rollout plan:
1. Deploy with default API_EMIT_LEGACY_AGENT_MSG=true.
2. Upgrade frontend to consume message.created and ignore agent.msg when message_id is present.
3. Flip API_EMIT_LEGACY_AGENT_MSG=false in production once verified.
4. Optionally remove legacy emission in a later cleanup.


## Chat Cookbook (Stage 11)

This section provides practical examples for working with the chat API and SSE from CLI and Python.

Curl: create message and run agent
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  -d '{"role":"user","format":"text","content":{"text":"Побудуй пайплайн для імпорту CSV"}}' \
  "http://localhost:8000/threads/$THREAD_ID/messages?run=1" | jq

Curl: subscribe to SSE with replay
curl -N \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  -H "Last-Event-ID: 0" \
  http://localhost:8000/threads/$THREAD_ID/events

Python: send message and consume SSE
```python
import asyncio, json, os
import httpx

API = os.getenv("API", "http://localhost:8000")
TOKEN = os.getenv("API_AUTH_TOKEN")
THREAD_ID = os.getenv("THREAD_ID")

headers = {"Content-Type": "application/json"}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

async def send_message(client: httpx.AsyncClient, text: str):
    r = await client.post(f"{API}/threads/{THREAD_ID}/messages?run=1", json={
        "role": "user",
        "format": "text",
        "content": {"text": text},
    }, headers=headers)
    r.raise_for_status()
    return r.json()

async def sse(client: httpx.AsyncClient, last_id: str | None = None):
    hdrs = {**headers, "Accept": "text/event-stream"}
    if last_id:
        hdrs["Last-Event-ID"] = last_id
    async with client.stream("GET", f"{API}/threads/{THREAD_ID}/events", headers=hdrs, timeout=None) as r:
        r.raise_for_status()
        async for line in r.aiter_lines():
            if not line:
                continue
            if line.startswith("event: "):
                ev = line.split(": ", 1)[1]
            elif line.startswith("data: "):
                data = line.split(": ", 1)[1]
                try:
                    payload = json.loads(data) if data else None
                except json.JSONDecodeError:
                    payload = data
                print(ev, payload)

async def main():
    async with httpx.AsyncClient(timeout=None) as client:
        await send_message(client, "Привіт, агенте!")
        # Run SSE listener concurrently for a short demo
        await asyncio.wait_for(sse(client, last_id="0"), timeout=10)

if __name__ == "__main__":
    asyncio.run(main())
```

Feature flag reminder
- API_EMIT_LEGACY_AGENT_MSG=true|false controls legacy agent.msg emission alongside message.created.

Troubleshooting
- 401 Unauthorized: send Authorization header if API_AUTH_TOKEN is configured.
- 204 from /events when passing Last-Event-ID: replay is not possible; reconnect without Last-Event-ID.
- Ensure reverse proxies do not buffer text/event-stream responses.
