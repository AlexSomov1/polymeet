from typing import Any, ClassVar

import structlog
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


async def ping(ctx: dict[str, Any]) -> str:
    """Служебная задача: проверка, что воркер берёт задания из очереди."""
    return "pong"


async def startup(ctx: dict[str, Any]) -> None:
    configure_logging(get_settings().log_level)
    logger.info("worker_started")


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("worker_stopped")


class WorkerSettings:
    """Настройки ARQ: ``arq app.workers.settings.WorkerSettings``."""

    functions: ClassVar[list[Any]] = [ping]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 1
    on_startup = startup
    on_shutdown = shutdown
