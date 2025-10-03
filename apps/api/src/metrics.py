from __future__ import annotations

from typing import Any
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

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

# Agent metrics
AGENT_RUNS = Counter(
    "agent_runs_total", "Agent runs started", ["mode"]  # mode: suggestion|fsm
)

# LLM metrics
LLM_CALLS = Counter(
    "llm_calls_total", "LLM calls", ["method", "provider", "status"]
)
LLM_LATENCY = Histogram(
    "llm_call_latency_seconds", "LLM call latency seconds", ["method", "provider"]
)


def prometheus_body() -> tuple[bytes, str]:
    """Return metrics body and content-type for FastAPI response."""
    return generate_latest(), CONTENT_TYPE_LATEST
