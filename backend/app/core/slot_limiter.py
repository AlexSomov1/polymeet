"""Distributed fixed-slot rate limiter with a process-local Redis fallback."""

import asyncio
import random
import time
from collections.abc import Callable
from typing import ClassVar

from redis.asyncio import Redis
from redis.exceptions import RedisError


class SlotLimitTimeout(Exception):
    """No slot was obtained within the allowed wait."""


class SlotLimiter:
    _locks: ClassVar[dict[str, asyncio.Lock]] = {}
    _next_at: ClassVar[dict[str, float]] = {}

    def __init__(
        self,
        redis: Redis,
        *,
        clock: Callable[[], float] = time.monotonic,
        max_wait: float = 30,
    ) -> None:
        self.redis = redis
        self.clock = clock
        self.max_wait = max_wait

    async def acquire(self, key: str, rps: float) -> None:
        if rps <= 0:
            raise ValueError("rps must be positive")
        interval = 1 / rps
        deadline = self.clock() + self.max_wait
        while True:
            try:
                if await self.redis.set(key, "1", nx=True, px=max(1, round(interval * 1000))):
                    return
                ttl = await self.redis.pttl(key)
            except (RedisError, OSError):
                await self._local_acquire(key, interval, deadline)
                return
            remaining = deadline - self.clock()
            if remaining <= 0:
                raise SlotLimitTimeout(f"Timed out waiting for {key}")
            delay = (ttl / 1000 if ttl > 0 else 0.01) + random.uniform(0, 0.005)
            await asyncio.sleep(min(delay, remaining))

    async def _local_acquire(self, key: str, interval: float, deadline: float) -> None:
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            wait = max(0, self._next_at.get(key, 0) - self.clock())
            if self.clock() + wait > deadline:
                raise SlotLimitTimeout(f"Timed out waiting for {key}")
            if wait:
                await asyncio.sleep(wait)
            self._next_at[key] = self.clock() + interval
