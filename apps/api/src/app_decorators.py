import time
from functools import wraps
from .app_metrics import UC_LATENCY, UC_SUCCESS, UC_ERROR

def instrument_uc(name: str):
    def _decor(fn):
        @wraps(fn)
        def inner(*a, **kw):
            start = time.perf_counter()
            try:
                out = fn(*a, **kw)
                UC_SUCCESS.labels(name).inc()
                return out
            except Exception as e:
                UC_ERROR.labels(name, e.__class__.__name__).inc()
                raise
            finally:
                UC_LATENCY.labels(name).observe(time.perf_counter() - start)
        return inner
    return _decor