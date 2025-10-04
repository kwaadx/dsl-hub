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
  - Health: GET /healthz
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
- API_LLM_PROVIDER and OpenAI-config variables if using a real LLM provider.


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
- Health check: GET /healthz probes DB connectivity; when DB is unavailable it returns HTTP 503 with a JSON body like {"status":"degraded","db":"unhealthy", "error": "..."}.
- HTTP metrics: path labels are normalized to route templates (e.g., /threads/{thread_id}) to keep Prometheus label cardinality low.
- POST /threads/{thread_id}/close is idempotent: repeated calls will not create new summaries if the thread is already closed; the latest existing summary and active flow summary are returned.
