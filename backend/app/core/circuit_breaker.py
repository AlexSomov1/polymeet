"""Redis-backed circuit breaker for external geocoding."""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import ClassVar, cast

from prometheus_client import Gauge
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import Settings

logger = logging.getLogger(__name__)
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state", "Circuit breaker state: closed=0, half-open=1, open=2", ["name"]
)


class BreakerState(StrEnum):
    CLOSED = "closed"
    HALF_OPEN = "half_open"
    OPEN = "open"


_STATE_VALUE = {BreakerState.CLOSED: 0, BreakerState.HALF_OPEN: 1, BreakerState.OPEN: 2}


@dataclass
class _LocalState:
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    state: BreakerState = BreakerState.CLOSED
    open_until: float = 0
    consecutive: int = 0
    counts: dict[int, tuple[int, int]] = field(default_factory=dict)
    probe: bool = False
    last_warning: float = float("-inf")


class CircuitBreaker:
    _local_states: ClassVar[dict[str, _LocalState]] = {}

    def __init__(
        self,
        name: str,
        settings: Settings,
        redis: Redis,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.name = name
        self.settings = settings
        self.redis = redis
        self.clock = clock
        self.key = f"cb:{name}"
        self.probe_key = f"{self.key}:probe"
        self._local = self._local_states.setdefault(name, _LocalState())
        self._metric(self._local.state)

    def _metric(self, state: BreakerState) -> None:
        CIRCUIT_BREAKER_STATE.labels(self.name).set(_STATE_VALUE[state])

    def _warn(self) -> None:
        now = self.clock()
        if now - self._local.last_warning >= 60:
            logger.warning("Circuit breaker %s uses local state: Redis unavailable", self.name)
            self._local.last_warning = now

    def _bucket(self) -> int:
        return int(self.clock() // self.settings.cb_window_sec)

    async def _hash(self) -> dict[str, str]:
        return await cast("Awaitable[dict[str, str]]", self.redis.hgetall(self.key))

    async def _set_hash(self, values: dict[str, str]) -> None:
        await cast("Awaitable[int]", self.redis.hset(self.key, mapping=values))

    async def _add_consecutive(self) -> int:
        return await cast("Awaitable[int]", self.redis.hincrby(self.key, "consecutive", 1))

    async def _increment(self, kind: str) -> int:
        key = f"{self.key}:w:{self._bucket()}:{kind}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, self.settings.cb_window_sec * 2)
        return int(count)

    async def _counts(self) -> tuple[int, int]:
        prefix = f"{self.key}:w:{self._bucket()}"
        values = await self.redis.mget(f"{prefix}:fail", f"{prefix}:ok")
        return int(values[0] or 0), int(values[1] or 0)

    def _should_open(self, consecutive: int, failed: int, succeeded: int) -> bool:
        total = failed + succeeded
        return consecutive >= self.settings.cb_fail_max or (
            total >= self.settings.cb_window_min_calls
            and failed / total >= self.settings.cb_window_fail_rate
        )

    async def state(self) -> BreakerState:
        try:
            values = await self._hash()
            current = BreakerState(values.get("state", BreakerState.CLOSED))
            if current == BreakerState.OPEN and self.clock() * 1000 >= int(
                values.get("open_until_ms", 0)
            ):
                current = BreakerState.HALF_OPEN
            self._metric(current)
            return current
        except (RedisError, OSError):
            self._warn()
            async with self._local.lock:
                current = self._local.state
                if current == BreakerState.OPEN and self.clock() >= self._local.open_until:
                    current = BreakerState.HALF_OPEN
                self._metric(current)
                return current

    async def allow(self) -> bool:
        try:
            values = await self._hash()
            current = BreakerState(values.get("state", BreakerState.CLOSED))
            if current == BreakerState.CLOSED:
                self._metric(current)
                return True
            if current == BreakerState.OPEN and self.clock() * 1000 < int(
                values.get("open_until_ms", 0)
            ):
                self._metric(current)
                return False
            acquired = bool(await self.redis.set(self.probe_key, "1", nx=True, px=10000))
            if acquired:
                await self._set_hash({"state": BreakerState.HALF_OPEN})
            self._metric(BreakerState.HALF_OPEN)
            return acquired
        except (RedisError, OSError):
            self._warn()
            async with self._local.lock:
                if self._local.state == BreakerState.CLOSED:
                    self._metric(BreakerState.CLOSED)
                    return True
                if self._local.state == BreakerState.OPEN and self.clock() < self._local.open_until:
                    self._metric(BreakerState.OPEN)
                    return False
                if self._local.probe:
                    return False
                self._local.probe = True
                self._local.state = BreakerState.HALF_OPEN
                self._metric(BreakerState.HALF_OPEN)
                return True

    async def record_success(self) -> None:
        try:
            values = await self._hash()
            if values.get("state") == BreakerState.OPEN:
                self._metric(BreakerState.OPEN)
                return
            if values.get("state") == BreakerState.HALF_OPEN:
                await self._set_hash({"state": BreakerState.CLOSED, "consecutive": "0"})
                await self.redis.delete(self.probe_key)
            else:
                await self._set_hash({"consecutive": "0"})
                await self._increment("ok")
                failed, succeeded = await self._counts()
                if self._should_open(0, failed, succeeded):
                    await self._open_remote()
                    return
            self._metric(BreakerState.CLOSED)
        except (RedisError, OSError):
            self._warn()
            async with self._local.lock:
                if self._local.state == BreakerState.OPEN:
                    return
                if self._local.state == BreakerState.HALF_OPEN:
                    self._local.probe = False
                    self._local.state = BreakerState.CLOSED
                else:
                    bucket = self._bucket()
                    fail, ok = self._local.counts.get(bucket, (0, 0))
                    self._local.counts = {bucket: (fail, ok + 1)}
                    if self._should_open(0, fail, ok + 1):
                        self._open_local()
                        return
                self._local.consecutive = 0
                self._metric(BreakerState.CLOSED)

    async def record_failure(self) -> None:
        try:
            values = await self._hash()
            if values.get("state") == BreakerState.OPEN:
                self._metric(BreakerState.OPEN)
                return
            if values.get("state") == BreakerState.HALF_OPEN:
                await self._open_remote()
                return
            consecutive = await self._add_consecutive()
            await self._increment("fail")
            failed, succeeded = await self._counts()
            if self._should_open(consecutive, failed, succeeded):
                await self._open_remote()
            else:
                self._metric(BreakerState.CLOSED)
        except (RedisError, OSError):
            self._warn()
            async with self._local.lock:
                if self._local.state == BreakerState.OPEN:
                    return
                if self._local.state == BreakerState.HALF_OPEN:
                    self._open_local()
                    return
                self._local.consecutive += 1
                bucket = self._bucket()
                fail, ok = self._local.counts.get(bucket, (0, 0))
                fail += 1
                self._local.counts = {bucket: (fail, ok)}
                if self._should_open(self._local.consecutive, fail, ok):
                    self._open_local()

    async def _open_remote(self) -> None:
        await self._set_hash(
            {
                "state": BreakerState.OPEN,
                "open_until_ms": str(int((self.clock() + self.settings.cb_open_seconds) * 1000)),
            },
        )
        await self.redis.delete(self.probe_key)
        self._metric(BreakerState.OPEN)

    def _open_local(self) -> None:
        self._local.state = BreakerState.OPEN
        self._local.open_until = self.clock() + self.settings.cb_open_seconds
        self._local.probe = False
        self._metric(BreakerState.OPEN)
