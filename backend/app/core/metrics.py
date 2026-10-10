from collections.abc import Callable
from functools import cache

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from prometheus_fastapi_instrumentator.metrics import Info

LATENCY_BUCKETS = (0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.5, 1, 2)


@cache
def _http_metrics() -> Callable[[Info], None]:
    # Метрики живут в глобальном реестре и создаются один раз на процесс: иначе
    # второе приложение (например, в тестах) получит ошибку дубликата и не будет их писать.
    instrumentation = metrics.default(latency_lowr_buckets=LATENCY_BUCKETS)
    if instrumentation is None:
        raise RuntimeError("метрики HTTP уже зарегистрированы вне setup_metrics")
    return instrumentation


def setup_metrics(app: FastAPI) -> None:
    """Метрики HTTP и эндпоинт ``/metrics`` (не попадает в OpenAPI)."""
    instrumentator = Instrumentator(excluded_handlers=["^/metrics$", "^/health"])
    instrumentator.add(_http_metrics())
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=False)
