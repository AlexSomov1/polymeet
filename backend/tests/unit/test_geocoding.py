import asyncio
import hashlib
import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import fakeredis.aioredis
import httpx
import pytest
import respx
from redis.exceptions import ConnectionError as RedisConnectionError

from app.clients.nominatim import GeocoderError, GeocoderUnavailable, GeoResult, NominatimClient
from app.core.circuit_breaker import BreakerState, CircuitBreaker
from app.core.slot_limiter import SlotLimiter
from app.services.geocoding_service import (
    GeocodingService,
    GeoOutcomeStatus,
    address_hash,
    normalize_address,
)
from tests.conftest import make_settings


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("  Санкт-Петербург  ", "санкт-петербург"),
        ("Ёлочная улица", "елочная улица"),
        ("ＡБВ\t  Ёж", "aбв еж"),
        ("Москва\n  Центр", "москва центр"),
    ],
)
def test_normalize_address(source: str, expected: str) -> None:
    assert normalize_address(source) == expected
    assert address_hash(source) == hashlib.sha256(expected.encode()).hexdigest()


class CountingLimiter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, float]] = []

    async def acquire(self, key: str, rps: float) -> None:
        self.calls.append((key, rps))


@pytest.mark.asyncio
async def test_nominatim_request_and_not_found() -> None:
    settings = make_settings(geocoder_base_url="https://geo.test", geocoder_rps=1)
    limiter = CountingLimiter()
    with respx.mock:
        route = respx.get("https://geo.test/search").mock(
            return_value=httpx.Response(
                200, json=[{"lat": "59.93", "lon": "30.31", "display_name": "Невский проспект"}]
            )
        )
        async with httpx.AsyncClient() as http:
            client = NominatimClient(settings, http, limiter)  # type: ignore[arg-type]
            result = await client.search("Невский")
            assert result == GeoResult(59.93, 30.31, "Невский проспект")
            request = route.calls.last.request
            assert request.url.params["q"] == "Невский"
            assert request.url.params["format"] == "jsonv2"
            assert request.url.params["limit"] == "1"
            assert request.url.params["accept-language"] == "ru"
            assert request.headers["User-Agent"] == settings.geocoder_user_agent
            route.mock(return_value=httpx.Response(200, json=[]))
            assert await client.search("нет адреса") is None
    assert len(limiter.calls) == 2


@pytest.mark.asyncio
async def test_nominatim_retries_each_take_a_slot() -> None:
    settings = make_settings(geocoder_base_url="https://geo.test", geocoder_retries=2)
    limiter = CountingLimiter()
    pauses: list[float] = []

    async def no_sleep(seconds: float) -> None:
        pauses.append(seconds)

    with respx.mock:
        route = respx.get("https://geo.test/search").mock(return_value=httpx.Response(503))
        async with httpx.AsyncClient() as http:
            client = NominatimClient(settings, http, limiter, sleep=no_sleep)  # type: ignore[arg-type]
            with pytest.raises(GeocoderUnavailable):
                await client.search("адрес")
            assert route.call_count == 3
            assert len(limiter.calls) == 3
            assert 0.3 <= pauses[0] < 0.4
            assert 0.6 <= pauses[1] < 0.7
            route.mock(return_value=httpx.Response(400))
            with pytest.raises(GeocoderError):
                await client.search("адрес")
            assert route.call_count == 4


@pytest.mark.asyncio
async def test_slot_limiter_distributed_and_local_fallback() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    limiter = SlotLimiter(redis)
    started = time.monotonic()
    await asyncio.gather(*(limiter.acquire("test:slot", 10) for _ in range(3)))
    assert time.monotonic() - started >= 0.19

    broken = AsyncMock()
    broken.set.side_effect = RedisConnectionError("down")
    local = SlotLimiter(broken)
    second_local = SlotLimiter(broken)
    started = time.monotonic()
    await asyncio.gather(
        local.acquire("test:local", 10),
        second_local.acquire("test:local", 10),
        local.acquire("test:local", 10),
    )
    assert time.monotonic() - started >= 0.19
    await redis.aclose()


@pytest.mark.asyncio
async def test_circuit_breaker_consecutive_and_single_probe() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    now = [1000.0]
    breaker = CircuitBreaker("geo-test", make_settings(), redis, clock=lambda: now[0])
    for _ in range(5):
        await breaker.record_failure()
    assert await breaker.state() == BreakerState.OPEN
    assert not await breaker.allow()
    now[0] += 61
    allowed = await asyncio.gather(*(breaker.allow() for _ in range(10)))
    assert allowed.count(True) == 1
    assert await breaker.state() == BreakerState.HALF_OPEN
    await breaker.record_success()
    assert await breaker.state() == BreakerState.CLOSED
    await redis.aclose()


@pytest.mark.asyncio
async def test_circuit_breaker_failure_rate_and_failed_probe() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    now = [2000.0]
    breaker = CircuitBreaker("rate", make_settings(), redis, clock=lambda: now[0])
    for _ in range(4):
        await breaker.record_failure()
        await breaker.record_success()
    await breaker.record_failure()
    assert await breaker.state() == BreakerState.CLOSED
    await breaker.record_success()
    assert await breaker.state() == BreakerState.OPEN
    now[0] += 61
    assert await breaker.allow()
    await breaker.record_failure()
    assert await breaker.state() == BreakerState.OPEN
    await redis.aclose()


@pytest.mark.asyncio
async def test_circuit_breaker_local_fallback() -> None:
    broken = AsyncMock()
    broken.hgetall.side_effect = RedisConnectionError("down")
    breaker = CircuitBreaker("fallback", make_settings(), broken)
    for _ in range(5):
        await breaker.record_failure()
    assert await breaker.state() == BreakerState.OPEN
    assert not await breaker.allow()
    another = CircuitBreaker("fallback", make_settings(), broken)
    assert not await another.allow()


@pytest.mark.asyncio
async def test_geocoding_cache_l1_l2_and_lru() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    settings = make_settings()
    session = AsyncMock()
    client = AsyncMock()
    breaker = CircuitBreaker("cache-test", settings, redis)
    service = GeocodingService(settings, session, redis, client, breaker)
    result = GeoResult(59.9, 30.3, "Невский проспект")
    key = address_hash("Невский")
    await redis.set(
        f"geo:{key}",
        json.dumps({"lat": result.lat, "lon": result.lon, "address_norm": result.address_norm}),
    )
    assert await service.lookup("  НЕВСКИЙ  ") == result
    session.scalar.assert_not_awaited()
    client.search.assert_not_awaited()

    await redis.delete(f"geo:{key}")
    row = SimpleNamespace(
        lat=result.lat, lon=result.lon, address_norm=result.address_norm, hit_count=0
    )
    session.scalar.return_value = row
    assert await service.lookup("Невский") == result
    assert row.hit_count == 1
    assert await redis.get(f"geo:{key}") is not None

    broken = AsyncMock()
    broken.get.side_effect = RedisConnectionError("down")
    degraded = GeocodingService(settings, session, broken, client, breaker)
    session.scalar.reset_mock()
    assert await degraded.lookup("Невский") == result
    session.scalar.assert_not_awaited()
    await redis.aclose()


@pytest.mark.asyncio
async def test_geocoding_fetch_outcomes() -> None:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    settings = make_settings()
    session = AsyncMock()
    client = AsyncMock()
    breaker = CircuitBreaker("outcomes", settings, redis)
    service = GeocodingService(settings, session, redis, client, breaker)
    client.search.return_value = GeoResult(59.9, 30.3, "Невский")
    outcome = await service.fetch_and_store("Невский")
    assert outcome.status == GeoOutcomeStatus.FOUND
    session.execute.assert_awaited_once()
    assert await redis.get(f"geo:{address_hash('Невский')}") is not None

    client.search.return_value = None
    assert (await service.fetch_and_store("нет")).status == GeoOutcomeStatus.NOT_FOUND
    client.search.side_effect = GeocoderUnavailable("503")
    assert (await service.fetch_and_store("ошибка")).status == GeoOutcomeStatus.UNAVAILABLE
    await redis.aclose()
