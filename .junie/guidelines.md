# Project Guidelines

## Project Overview
DSL Hub is a monorepo for building, running, and observing domain‑specific language (DSL) workflows. It includes a Python FastAPI backend, a Vue 3 + Vite web frontend, and a PostgreSQL database, all orchestrated via Docker Compose. Optional worker services (a Go runtime and Python drivers) are present but disabled by default.

## Repository Layout (top level)
- apps/api: FastAPI backend service
  - src/main.py: FastAPI app entrypoint (served by Uvicorn)
  - alembic/: Database migrations (managed via Alembic)
  - seed.py: Development/seed data bootstrap
- apps/web: Vue 3 + Vite frontend application
- apps/runtime: Go worker (optional, currently commented out in docker-compose)
- apps/drivers: Python drivers for external integrations (optional)
- apps/db: Database-related utilities (if any)
- schemas: Shared schemas for validation/contracts
- docker-compose.yml: Local orchestration of DB, API, Web, and Dozzle

## Running Locally (Docker)
- Configuration: The stack reads .env and .env.local. Put your local overrides into .env.local.
- Start services: docker-compose up
- Default endpoints:
  - Web: http://localhost:${WEB_PORT:-3000}
  - API: http://localhost:${API_PORT:-8000}
  - Health: http://localhost:${API_PORT:-8000}/healthz
  - Metrics: http://localhost:${API_PORT:-8000}/metrics
  - Dozzle (logs): http://localhost:8080

## Notes for Contributors
- Migrations run automatically on API start (alembic upgrade head); keep migrations in sync with models.
- Prefer small, focused changes. When modifying API behavior, add/update Pydantic DTOs in apps/api/src/dto.py as needed.
- Keep this document up to date if structure or run commands change.
