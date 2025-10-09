Purpose
This file defines development rules for DSL Hub. It is not a README. It serves as instruction for the LLM (Junie or any other development agent) that generates or edits code inside the project. The agent must follow these rules exactly.

0. Database as source of truth

* Always rely on the existing initial migration: /apps/api/alembic/versions/9f0b7b2c6f3a_init.py and SQL in versions/sql.
* Extensions used: pgcrypto, pg_trgm, citext.
* Helper functions: set_updated_at, set_archived_ts.
* Key entities: flow, thread, message, schema_def, pipeline, generation_run, validation_issue, agent_log, summaries, context_snapshot, summary_run, schema_upgrade_plan, pipeline_upgrade_run, compat_rule.
* Maintain single-flow integrity. Example: thread.result_pipeline_id must reference a pipeline of the same flow.

1. Backend (FastAPI)
   1.0 Architecture

* Follow SOLID and DDD at package level: routers, services, repositories, dto, middleware, agent, sse.
* Routers only validate and delegate. No business logic in routers.
* Services hold domain logic. Repositories handle database only.
* All functions and DTOs must be strictly typed.
* JSON columns are jsonb. In code: dict[str, Any]. Validate content in services.
* Use Idempotency-Key for write routes.
* Every new route must have tests.
* Return standardized error objects with code and message.
* Authentication is optional; if present, middleware validates token and injects user context.
* SSE events must preserve order and allow buffering.

1.1 Code style

* Use ruff and black formatters. Run mypy when possible.
* Code must be self-explanatory. Do not use comments unless required.
* Functions should be small and clear. Names must reveal intent.
* Error handling: raise domain-specific exceptions or normalized HTTPException.

1.2 Transactions

* Repository methods receive active Session and never close it. Session lifecycle is handled by FastAPI dependencies.
* Integrity and invariants belong to database constraints and triggers.
* When violation occurs, raise user-friendly error.

1.3 Performance

* Use existing indexes. Avoid full JSON scans.
* Always paginate large collections.

1.4 Tests

* Each route must have success, validation, and auth tests.
* Where applicable include idempotency and SSE tests.
* Run tests only inside the api container using docker exec dsl-hub-api pytest -q.
* Prefer fast unit tests without I/O. Integration tests through docker-compose.

2. Frontend (Vue 3 + Vite + PrimeVue)

* Use Composition API and script setup.
* Types go in @/types.
* Logic extracted into composables/.
* Use Pinia only if necessary, otherwise local state.
* Do not manually import PrimeVue components if auto-import is configured.
* Naming: Base* for base components, App* for roots, *View for route screens.
* Use scoped or module CSS. Avoid global styles.
* Use strict ESLint and Prettier.
* API client in @/api. It must send Idempotency-Key on writes.
* SSE logic implemented in a shared helper, not scattered.

3. Agent behavior

* The agent follows a defined graph in apps/api/src/agent/graph.py.
* States: init → search_existing → generate → self_check → hard_validate → persist → publish → finish.
* On each stage: runs_repo.tick is called, SSE events are emitted.
* Agent uses LLMClientProtocol, ValidationService, PipelineService, SimilarityService.
* Never depend on specific LLM provider. Use the protocol interface.
* Every new branch or behavior must include tests.

4. Testing levels

* Unit: services, agent nodes, repositories.
* Integration: FastAPI routes, SSE, idempotency, auth.
* Coverage must include positive and negative paths.

5. Naming conventions

* Backend: snake_case for files and functions, PascalCase for classes.
* DTO: PascalCase, e.g., FlowOut, CreateFlow.
* Frontend: PascalCase.vue for components, useSomething.ts for composables.

6. Git and PR

* Branch types: feat/*, fix/*, chore/*, docs/*, test/*.
* Commits: Conventional Commits format.
* Pull request must contain: reason, what changed, tests, lint, compatibility.
* Do not touch README.md in tech PRs.

7. Security and performance

* Secrets from environment only. Never commit keys.
* Enforce rate and size limits.
* Close SSE connections properly.
* Validate all external JSON inputs.
* Logs must be PII-safe.

8. Documentation

* guidelines.txt defines standards (this file).
* AGENT.md defines agent state machine and behavior.
* README.md is for users only.

9. Merge checklist

* Structure routers → services → repositories → dto preserved.
* Names clear, no comments.
* Tests exist and pass.
* Linters and typing pass.
* Database invariants preserved.
* Pagination and idempotency present where needed.

10. References

* Migrations: apps/api/alembic/versions.
* Agent: apps/api/src/agent/graph.py.
* Flow routes: apps/api/src/routers/flows.py.
* Tests: apps/api/src/tests.

This file is the instruction set for the development LLM. When generating or editing code for DSL Hub, the model must follow these rules exactly.
