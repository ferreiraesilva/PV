from __future__ import annotations

import time

from prometheus_client import CollectorRegistry, Counter, Histogram

from app.core.config import get_settings

settings = get_settings()
registry = CollectorRegistry()

REQUEST_COUNTER = Counter(
    "requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    namespace=settings.metrics_namespace,
    registry=registry,
)

ERROR_COUNTER = Counter(
    "errors_total",
    "Total number of errors returned by the API",
    ["code", "endpoint"],
    namespace=settings.metrics_namespace,
    registry=registry,
)

RATE_LIMIT_COUNTER = Counter(
    "rate_limit_hits_total",
    "Number of requests blocked by the rate limiter",
    ["endpoint"],
    namespace=settings.metrics_namespace,
    registry=registry,
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Latency of HTTP requests",
    ["endpoint"],
    namespace=settings.metrics_namespace,
    registry=registry,
)


def observe_request(endpoint: str, latency_seconds: float) -> None:
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(latency_seconds)


def now_seconds() -> float:
    return time.perf_counter()
