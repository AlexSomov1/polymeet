from unittest.mock import AsyncMock

import pytest
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.clients.nominatim import GeoResult
from app.core.circuit_breaker import CircuitBreaker
from app.core.config import Settings
from app.models.geocode_cache import GeocodeCache
from app.services.geocoding_service import GeocodingService, GeoOutcomeStatus, address_hash


@pytest.mark.asyncio
async def test_geocode_cache_upsert_and_hit_count(
    engine: AsyncEngine, redis: Redis, settings: Settings
) -> None:
    client = AsyncMock()
    client.search.return_value = GeoResult(59.93, 30.31, "Санкт-Петербург, Невский")
    breaker = CircuitBreaker("integration-geocoder", settings, redis)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        service = GeocodingService(settings, session, redis, client, breaker)
        assert (await service.fetch_and_store("  Невский  ")).status == GeoOutcomeStatus.FOUND
        await session.commit()

    async with AsyncSession(engine, expire_on_commit=False) as session:
        service = GeocodingService(settings, session, redis, client, breaker)
        assert await service.lookup("НЕВСКИЙ") == GeoResult(
            59.93, 30.31, "Санкт-Петербург, Невский"
        )
        await redis.delete(f"geo:{address_hash('Невский')}")
        assert await service.lookup("Невский") == GeoResult(
            59.93, 30.31, "Санкт-Петербург, Невский"
        )
        await session.commit()

    client.search.return_value = GeoResult(59.94, 30.32, "Санкт-Петербург, Невский, 2")
    async with AsyncSession(engine, expire_on_commit=False) as session:
        service = GeocodingService(settings, session, redis, client, breaker)
        assert (await service.fetch_and_store("невский")).status == GeoOutcomeStatus.FOUND
        await session.commit()

    async with AsyncSession(engine) as session:
        rows = list(
            await session.scalars(
                select(GeocodeCache).where(GeocodeCache.query_hash == address_hash("Невский"))
            )
        )
        assert len(rows) == 1
        assert rows[0].lat == 59.94
        assert rows[0].hit_count == 1
