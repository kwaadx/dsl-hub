from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
try:
    # If OTLP is configured, prefer it
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    _has_otlp = True
except Exception:
    _has_otlp = False

_tracer = None

def init_tracer(service_name: str = "dslhub-api"):
    global _tracer
    provider = TracerProvider()
    if _has_otlp:
        exporter = OTLPSpanExporter()  # uses env OTEL_EXPORTER_OTLP_ENDPOINT
    else:
        exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name)

def get_tracer():
    global _tracer
    if _tracer is None:
        init_tracer()
    return _tracer

def traced(span_name: str):
    def _wrap(fn):
        def _sync(*a, **kw):
            tracer = get_tracer()
            with tracer.start_as_current_span(span_name):
                return fn(*a, **kw)
        async def _async(*a, **kw):
            tracer = get_tracer()
            with tracer.start_as_current_span(span_name):
                return await fn(*a, **kw)
        # pick wrapper based on coroutine
        return _async if getattr(fn, "__code__", None) and "async" in str(type(fn)) else _sync
    return _wrap