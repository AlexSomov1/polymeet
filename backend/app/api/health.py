import asyncio
from typing import Annotated, Literal

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.redis import get_redis

CHECK_TIMEOUT_SEC = 1.0

router = APIRouter(tags=["health"])
logger = structlog.get_logger(__name__)

CheckResult = Literal["ok", "down"]


@router.get("/health", summary="Процесс жив")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _check_db(session: AsyncSession) -> CheckResult:
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SEC):
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("health_check_failed", dependency="db", error=type(exc).__name__)
        return "down"
    return "ok"


async def _check_redis(redis: Redis) -> CheckResult:
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SEC):
            await redis.ping()
    except Exception as exc:
        logger.warning("health_check_failed", dependency="redis", error=type(exc).__name__)
        return "down"
    return "ok"


@router.get(
    "/health/ready",
    summary="Готовность принимать запросы",
    description=(
        "Проверяет PostgreSQL и Redis. Без PostgreSQL сервис не готов (503); "
        "без Redis работает с деградацией (200, `degraded`)."
    ),
)
async def health_ready(
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> JSONResponse:
    db_state, redis_state = await asyncio.gather(_check_db(session), _check_redis(redis))
    if db_state == "down":
        status, http_status = "unavailable", 503
    elif redis_state == "down":
        status, http_status = "degraded", 200
    else:
        status, http_status = "ok", 200
    return JSONResponse(
        {"status": status, "db": db_state, "redis": redis_state},
        status_code=http_status,
    )
