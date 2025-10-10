from prometheus_client import Counter, Histogram

UC_LATENCY = Histogram("dslhub_uc_latency_seconds", "Use-case latency (s)", ["uc"])
UC_SUCCESS = Counter("dslhub_uc_success_total", "Use-case success count", ["uc"])
UC_ERROR = Counter("dslhub_uc_error_total", "Use-case error count", ["uc","kind"])