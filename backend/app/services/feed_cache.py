"""Кэш первой страницы ленты в Redis.

Ключ ``feed:v{version}:{sha1}``: ``sha1`` — от параметров запроса, ``version`` — счётчик
``feed:version``. ``bump()`` увеличивает версию, и старые ключи становятся недостижимы,
пока не истекут сами. Любая ошибка Redis обходит кэш: лента отвечает из базы.
"""

import hashlib
import json
from collections.abc import Mapping

import structlog
from prometheus_client import Counter
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.logging import bind_request_context

FEED_CACHE = Counter("feed_cache_total", "Feed first page cache lookups", ["result"])

VERSION_KEY = "feed:version"

logger = structlog.get_logger(__name__)


def params_hash(params: Mapping[str, object]) -> str:
    """Хэш параметров запроса: порядок не важен, значения ``None`` не учитываются."""
    present = {name: value for name, value in params.items() if value is not None}
    payload = json.dumps(present, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


class FeedCache:
    def __init__(self, redis: Redis, ttl_sec: int) -> None:
        self._redis = redis
        self._ttl_sec = ttl_sec

    async def _key(self, params: Mapping[str, object]) -> str:
        version = await self._redis.get(VERSION_KEY)
        return f"feed:v{int(version or 0)}:{params_hash(params)}"

    async def get(self, params: Mapping[str, object]) -> str | None:
        """JSON страницы или ``None``; результат идёт в лог запроса и в метрику."""
        try:
            cached: str | None = await self._redis.get(await self._key(params))
        except (RedisError, OSError) as exc:
            logger.warning("feed_cache_unavailable", error=str(exc))
            FEED_CACHE.labels("error").inc()
            bind_request_context(cache="miss")
            return None
        result = "hit" if cached is not None else "miss"
        FEED_CACHE.labels(result).inc()
        bind_request_context(cache=result)
        return cached

    async def set(self, params: Mapping[str, object], payload: str) -> None:
        try:
            await self._redis.set(await self._key(params), payload, ex=self._ttl_sec)
        except (RedisError, OSError) as exc:
            logger.warning("feed_cache_unavailable", error=str(exc))

    async def bump(self) -> None:
        """Делает недостижимыми все закэшированные страницы. Ошибку только логирует."""
        try:
            await self._redis.incr(VERSION_KEY)
        except (RedisError, OSError) as exc:
            logger.warning("feed_cache_bump_failed", error=str(exc))
