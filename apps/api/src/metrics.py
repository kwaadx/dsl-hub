from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, CONTENT_TYPE_LATEST, generate_latest

# HTTP metrics
HTTP_REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request duration seconds", ["method", "path"]
)

# SSE metrics
SSE_EVENTS = Counter(
    "sse_events_total", "Total SSE events published", ["event"]
)
SSE_CONNECTIONS = Counter(
    "sse_connections_total", "SSE connections open/close", ["action"]
)
SSE_SESSION_SECONDS = Histogram(
    "sse_session_duration_seconds", "Duration of SSE connections in seconds"
)

# Agent metrics
AGENT_RUNS = Counter(
    "agent_runs_total", "Agent runs started", ["mode"]  # mode: suggestion|fsm
)
# Duration of complete agent runs (init -> finish)
AGENT_RUN_SECONDS = Histogram(
    "agent_run_duration_seconds", "Duration of agent runs in seconds", ["status"]
)
# Count of runs that failed with an exception (outside normal failed stage)
AGENT_RUN_ERRORS = Counter(
    "agent_run_errors_total", "Total agent runs that errored unexpectedly"
)

# Messages (chat) metrics
MESSAGES_CREATED = Counter(
    "messages_created_total", "Messages created and persisted to DB", ["role", "source"]  # source: route|fsm
)

# LLM metrics
LLM_CALLS = Counter(
    "llm_calls_total", "LLM calls", ["method", "provider", "status"]
)
LLM_LATENCY = Histogram(
    "llm_call_latency_seconds", "LLM call latency seconds", ["method", "provider"]
)

# Idempotency cache
IDEMPOTENCY_CACHE_ENTRIES = Gauge(
    "idempotency_cache_entries", "Number of entries in idempotency cache"
)

def prometheus_body() -> tuple[bytes, str]:
    """Return metrics body and content-type for FastAPI response."""
    return generate_latest(), CONTENT_TYPE_LATEST
