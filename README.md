# DSL Hub

A modern platform for domain-specific language development and execution.

## Overview

DSL Hub is a comprehensive platform that allows users to create, manage, and execute domain-specific languages. It consists of a Vue.js frontend and a FastAPI backend, providing a seamless experience for DSL development.

## Features

- Interactive DSL editor with syntax highlighting
- Real-time DSL execution and visualization
- Version control for DSL definitions
- User management and access control
- API integration for external systems

## Architecture

The project is structured as a monorepo with the following components:

- `apps/web`: Vue.js frontend application
- `apps/agent`: FastAPI backend service
- `packages`: Shared libraries and utilities
- `schemas`: JSON Schema definitions for DSL validation

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.10+ (for local development)

## Getting Started

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/dsl-hub.git
   cd dsl-hub
   ```

2. Create a `.env.local` file with your local configuration:
   ```bash
   MODE=dev
   ```

3. Start the services:
   ```bash
   docker-compose up
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:5000

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/dsl-hub.git
   cd dsl-hub
   ```

2. Set up the frontend:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```

3. Set up the backend:
   ```bash
   cd apps/agent
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload --port 5000
   ```

## Environment Variables

The application can be configured using environment variables. Create a `.env.local` file in the root directory to override the default settings.

See the `.env` file for available configuration options.

## Observability (Prometheus metrics)

The backend exposes Prometheus metrics (GET /metrics). Key metrics for chat and agent runs:
- sse_events_total{event}
- sse_connections_total{action}
- sse_session_duration_seconds (histogram)
- agent_runs_total{mode}
- agent_run_duration_seconds{status} (histogram)
- agent_run_errors_total
- messages_created_total{role,source}

Suggested alerts (examples):
- agent_run_errors_total increases > 0 over 5m
- sse_session_duration_seconds p50 < 2s for 10m (frequent disconnects)
- messages_created_total{role="assistant"} drops to 0 while user messages are created

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


---

Backend quick start (Docker)
- The stack reads .env and .env.local. Put local overrides into .env.local.
- Start services: docker-compose up
- Default endpoints:
  - Web: http://localhost:${WEB_PORT:-3000}
  - API: http://localhost:${API_PORT:-8000}
  - Health: GET /health
  - Metrics: GET /metrics

CORS and Auth
- Configure allowed frontend origins via API_CORS_ORIGINS (CSV). Example:
  API_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
  Use * to allow all (development only).
- If API_AUTH_TOKEN is set, all POST/PUT/PATCH/DELETE require header:
  Authorization: Bearer <token>
- For POST requests, provide Idempotency-Key: <uuid> to make operations safe to retry.

SSE reconnection semantics
- Subscribe to thread events: GET /threads/{thread_id}/events (Server-Sent Events).
- On reconnect, send Last-Event-ID with the last received cursor (stringified integer):
  Last-Event-ID: 42
- If the server cannot replay from your Last-Event-ID (buffer expired), it returns 204 No Content.
  In this case, reconnect again WITHOUT Last-Event-ID to start a fresh stream.
- Keep-alive pings are sent periodically as event: ping.

Useful curl examples
- Create Flow
  curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_AUTH_TOKEN" \
    -H "Idempotency-Key: $(uuidgen)" \
    -d '{"slug":"demo","name":"Demo"}' \
    http://localhost:8000/flows

- Create Thread under Flow
  curl -X POST \
    -H "Authorization: Bearer $API_AUTH_TOKEN" \
    -H "Idempotency-Key: $(uuidgen)" \
    http://localhost:8000/flows/<flow_id>/threads

- Add Message to Thread
  curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_AUTH_TOKEN" \
    -H "Idempotency-Key: $(uuidgen)" \
    -d '{"role":"user","content":"Hello"}' \
    http://localhost:8000/threads/<thread_id>/messages

- Subscribe to SSE (with replay)
  curl -N -H "Last-Event-ID: 42" http://localhost:8000/threads/<thread_id>/events

- Run Agent on Thread
  curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_AUTH_TOKEN" \
    -d '{"user_message":"How to run?","options":{}}' \
    http://localhost:8000/threads/<thread_id>/agent/run

Environment variables (backend)
- API_CORS_ORIGINS: CSV list of allowed origins for CORS. Use * to allow all (dev only).
- API_AUTH_TOKEN: If set, write operations require Authorization: Bearer <token>.
- API_IDEMPOTENCY_TTL_SEC: TTL for idempotency cache (default 300 seconds).
- API_IDEMPOTENCY_CACHE_MAX: Max entries for idempotency cache (default 1000).
- API_SSE_PING_INTERVAL, API_SSE_BUFFER_TTL_SEC: SSE keepalive and replay window.
- API_SSE_BUFFER_MAXLEN: Max number of events retained in the SSE replay buffer (default 500).
- API_SCHEMA_CHANNEL: Active schema channel (default stable).
- API_MESSAGES_RATE_PER_MINUTE: Per-thread rate limit for POST /threads/{id}/messages over 60s window (default 30; set 0 to disable).
- API_MESSAGE_TEXT_MAX_LEN: Max length (characters) for text/markdown message content.text (default 4000).
- OpenAI configuration variables (OpenAI-only): API_OPENAI_API_KEY, API_OPENAI_MODEL, API_OPENAI_BASE_URL (optional).


Standardized error responses (backend)
- All errors follow a unified AppError shape from the global error handler.
- Typical cases you will encounter from the frontend:

401 Unauthorized (missing/invalid Authorization when API_AUTH_TOKEN is set)
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "code": "UNAUTHORIZED",
  "message": "Missing or invalid Authorization token",
  "status": 401,
  "details": []
}
```

404 Not Found (e.g., thread or pipeline not found)
```
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "code": "NOT_FOUND",
  "message": "Thread not found",
  "status": 404,
  "details": []
}
```

409 Conflict (Idempotency-Key reused with a different request body)
```
HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "code": "IDEMPOTENCY_KEY_REUSED",
  "message": "Idempotency-Key has already been used with a different request body",
  "status": 409,
  "details": [{"path": "/threads/<id>/messages"}]
}
```

Notes
- For POST endpoints, always send a unique Idempotency-Key to enable safe retries.
- When reconnecting to SSE with an outdated Last-Event-ID, the server returns 204 No Content; reconnect again without Last-Event-ID.
- Health check: GET /health probes DB connectivity; returns 200 when healthy and 503 when DB is unavailable.
- HTTP metrics: path labels are normalized to route templates (e.g., /threads/{thread_id}) to keep Prometheus label cardinality low.
- POST /threads/{thread_id}/close is idempotent: repeated calls will not create new summaries if the thread is already closed; the latest existing summary and active flow summary are returned.


## Chat API v1 (Stage 1: Contract)

This section defines the initial chat contract to move history to the backend while preserving SSE behavior. It is documentation-only for Stage 1. Subsequent stages will implement the endpoints and frontend changes.

### HTTP Endpoints

- GET /threads/{thread_id}/messages
  - Query params:
    - limit: integer (1..200, default 50)
    - before: optional cursor (message id or created_at ISO; exact cursor form will be finalized during Stage 2; recommended to start with id)
  - Response: 200 OK, JSON array of messages sorted by created_at ASC
  - Message shape:
    {
      "id": "<uuid>",
      "role": "user" | "assistant" | "system",
      "format": "text" | "markdown" | "json",
      "content": any,
      "created_at": "2025-10-08T20:11:22Z",
      "parent_id": "<uuid>" | null,
      "tool_name": string | null,
      "tool_result": any | null
    }

- POST /threads/{thread_id}/messages?run=1
  - Creates a user message in the thread and (if run=1) immediately starts the agent FSM for that thread.
  - Headers: 
    - Content-Type: application/json
    - Authorization: Bearer <token> (if API_AUTH_TOKEN configured)
    - Idempotency-Key: <uuid> (recommended)
  - Request body (MessageIn):
    {
      "role": "user",
      "format": "text",
      "content": {"text": "Привіт"},
      "parent_id": null
    }
  - Response: 201 Created
    {
      "id": "<uuid>",
      "created_at": "2025-10-08T20:11:22Z",
      "meta": {
        "run": {"run_id": "<uuid>", "status": "queued"}
      }
    }

- POST /threads/{thread_id}/agent/event
  - Accepts UI events from the frontend and acknowledges via SSE ui.ack events. Does not advance FSM (MVP).

- POST /threads/{thread_id}/agent/run
  - Legacy path to start the agent with an inline user_message. Will remain for compatibility; new flow should prefer POST /messages?run=1.

### SSE Events

All events are delivered via GET /threads/{thread_id}/events as text/event-stream. The server supports replay via Last-Event-ID and returns 204 when replay is not possible.

Core events:
- message.created
  {
    "message_id": "<uuid>",
    "role": "assistant" | "user" | "system",
    "format": "text" | "markdown" | "json",
    "content": any,
    "ts": 1699999999999
  }
- run.started { run_id, stage, ts }
- run.stage { run_id, stage, status, [error], ts }
- suggestion { ... , ts }
- issues { items: [...], ts }
- pipeline.created { pipeline_id, version, status, ts }
- pipeline.published { pipeline_id, version, ts }
- run.finished { run_id, status, [error], ts }
- ui.ack { kind, msg, event, ts }
- ping (heartbeat)

Note: During the transition period the backend may emit both message.created and agent.msg. Frontend should prefer message.created and ignore agent.msg if both are present for the same logical content.

### Curl examples

- Get last 50 messages
  curl -s \
    -H "Authorization: Bearer $API_AUTH_TOKEN" \
    http://localhost:8000/threads/<thread_id>/messages | jq

- Create a message and start agent
  curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_AUTH_TOKEN" \
    -H "Idempotency-Key: $(uuidgen)" \
    -d '{"role":"user","format":"text","content":{"text":"Згенеруй пайплайн"}}' \
    "http://localhost:8000/threads/<thread_id>/messages?run=1" | jq

- Subscribe to SSE with replay
  curl -N -H "Last-Event-ID: 42" http://localhost:8000/threads/<thread_id>/events


## Feature flag: legacy agent.msg SSE emission (Stage 10)

To support a safe rollout and backward compatibility, the backend now exposes a feature flag controlling the legacy SSE event `agent.msg`:

- Env var: API_EMIT_LEGACY_AGENT_MSG=true|false (default: true)
- Behavior:
  - When true (default), the backend emits both message.created (new) and agent.msg (legacy) for assistant/system messages produced by the agent FSM. This preserves compatibility with older frontends.
  - When false, the backend emits only message.created. The legacy agent.msg is disabled.

Recommended rollout steps:
1) Deploy backend with API_EMIT_LEGACY_AGENT_MSG=true (default) so both events are emitted.
2) Update frontend to consume message.created and ignore agent.msg when message_id is present (already implemented in Stage 7).
3) After verifying no consumers rely on agent.msg, set API_EMIT_LEGACY_AGENT_MSG=false in production.
4) After a deprecation window, you may remove the legacy emission code entirely.

Notes:
- User messages created via POST /threads/{id}/messages always emit message.created; a legacy agent.msg is not required for user messages.
- SSE reconnection and replay semantics remain unchanged.


## Chat end-to-end quickstart (Stage 11 examples)

This section provides a copy-paste friendly, end-to-end walkthrough for the new chat flow with the backend as the source of truth for history.

Prerequisites
- Backend running (docker-compose up) and accessible at http://localhost:${API_PORT:-8000}
- Optional: API auth token set via API_AUTH_TOKEN. If set, include Authorization: Bearer <token> in your requests.
- Recommended: use Idempotency-Key for POSTs so retries are safe.

Step 1. Create Flow
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  -d '{"slug":"demo","name":"Demo"}' \
  http://localhost:8000/flows | jq

Capture the returned flow id as FLOW_ID.

Step 2. Create Thread under the Flow
curl -s -X POST \
  -H "Idempotency-Key: $(uuidgen)" \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  http://localhost:8000/flows/$FLOW_ID/threads | jq

Capture the returned thread id as THREAD_ID.

Step 3. Open SSE stream (in a separate terminal)
# With replay from start (if any events already published)
curl -N -H "Last-Event-ID: 0" \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  http://localhost:8000/threads/$THREAD_ID/events

You will see event: ping periodically, and lifecycle/chat events for the thread.

Step 4. Send a user message and start the agent
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  -d '{"role":"user","format":"text","content":{"text":"Згенеруй пайплайн"}}' \
  "http://localhost:8000/threads/$THREAD_ID/messages?run=1" | jq

The SSE terminal should print a sequence like:
- event: run.started
- event: message.created (your user message)
- event: run.stage ...
- event: message.created (assistant/system outputs)
- event: run.finished

Step 5. Fetch persisted history
curl -s \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  http://localhost:8000/threads/$THREAD_ID/messages | jq

Notes
- If the SSE server returns 204 No Content when connecting with Last-Event-ID, reconnect without the header to start a fresh stream.
- To safely retry POSTs, reuse the same Idempotency-Key only with the same request body. Reusing it with a different body will return 409.


## Frontend developer guide (Chat) — Stage 11

Local dev
- cd apps/web; npm install; npm run dev
- Ensure the API base URL is configured via VITE_API_BASE_URL (default inferred by the app). Example .env.local for the root:
  VITE_API_BASE_URL=http://localhost:8000
- If API auth is enabled on the backend, pass the token as a prop to ThreadChat.vue or wire it from your auth state; it will be used for GET/POST and SSE.

Minimal usage
- Use the ThreadChat.vue component with props: threadId (required), optional flowId and token.
- History is loaded from GET /threads/{threadId}/messages on mount.
- Sending a message calls POST /threads/{threadId}/messages?run=1 and relies on SSE message.created for rendering.
- SSE reconnection uses Last-Event-ID with replay and handles 204 by resetting the cursor automatically.

Troubleshooting
- 401 Unauthorized: if API_AUTH_TOKEN is set, ensure you send Authorization: Bearer <token> on POST and SSE requests.
- 204 on SSE connect: your Last-Event-ID is outside the replay window. Reconnect without Last-Event-ID (our client does this automatically).
- Duplicate messages: the client deduplicates by message_id from message.created. Ensure your UI ignores legacy agent.msg when message_id is present.
- Proxies/load balancers: make sure they support Server-Sent Events (no buffering of text/event-stream, disable response buffering for the SSE path).


## Chat curl cheat sheet

- Create message without running agent
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  -d '{"role":"user","format":"text","content":{"text":"Hi"}}' \
  http://localhost:8000/threads/$THREAD_ID/messages | jq

- Paginate history (older messages before id)
curl -s \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  "http://localhost:8000/threads/$THREAD_ID/messages?limit=50&before=$MSG_ID" | jq

- Legacy start (not recommended)
curl -s -X POST \
  -H "Content-Type: application/json" \
  ${API_AUTH_TOKEN:+-H "Authorization: Bearer $API_AUTH_TOKEN"} \
  -d '{"user_message":{"role":"user","content":{"text":"..."},"format":"text"},"options":{}}' \
  http://localhost:8000/threads/$THREAD_ID/agent/run | jq


## Feature flag reminder (Stage 10)

- API_EMIT_LEGACY_AGENT_MSG=true|false controls whether legacy agent.msg SSE events are emitted alongside message.created. Default: true. Set to false after frontend migration.
