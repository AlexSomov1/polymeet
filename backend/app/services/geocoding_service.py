"""Cache-only lookup and remote geocoding. S09 wires this service to meeting jobs."""

import hashlib
import json
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from enum import StrEnum

from prometheus_client import Counter
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.nominatim import GeocoderError, GeocoderUnavailable, GeoResult, NominatimClient
from app.core.circuit_breaker import CircuitBreaker
from app.core.config import Settings
from app.models.geocode_cache import GeocodeCache

GEOCODER_REQUESTS = Counter("geocoder_requests_total", "Geocoder outcomes", ["result"])
GEO_CACHE = Counter("geo_cache_total", "Geocoder cache lookups", ["level"])
_LOCAL_GEO_LRU: OrderedDict[str, GeoResult] = OrderedDict()


def normalize_address(address: str) -> str:
    value = unicodedata.normalize("NFKC", address).casefold().replace("ё", "е")
    return " ".join(value.split())


def address_hash(address: str) -> str:
    return hashlib.sha256(normalize_address(address).encode("utf-8")).hexdigest()


class GeoOutcomeStatus(StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"
    BREAKER_OPEN = "breaker_open"


@dataclass(frozen=True)
class GeoOutcome:
    status: GeoOutcomeStatus
    result: GeoResult | None = None


class GeocodingService:
    def __init__(
        self,
        settings: Settings,
        session: AsyncSession,
        redis: Redis,
        client: NominatimClient,
        breaker: CircuitBreaker,
    ) -> None:
        self.settings = settings
        self.session = session
        self.redis = redis
        self.client = client
        self.breaker = breaker
        self._lru = _LOCAL_GEO_LRU

    def _remember(self, key: str, result: GeoResult) -> None:
        self._lru[key] = result
        self._lru.move_to_end(key)
        if len(self._lru) > 1000:
            self._lru.popitem(last=False)

    async def _write_l1(self, key: str, result: GeoResult) -> None:
        try:
            await self.redis.set(
                f"geo:{key}",
                json.dumps(
                    {"lat": result.lat, "lon": result.lon, "address_norm": result.address_norm}
                ),
                ex=self.settings.geo_cache_ttl_days * 86400,
            )
        except (RedisError, OSError):
            pass
        self._remember(key, result)

    async def lookup(self, address: str) -> GeoResult | None:
        key = address_hash(address)
        redis_failed = False
        try:
            raw = await self.redis.get(f"geo:{key}")
            if raw is not None:
                try:
                    value = json.loads(raw)
                    result = GeoResult(
                        lat=float(value["lat"]),
                        lon=float(value["lon"]),
                        address_norm=str(value["address_norm"]),
                    )
                    self._remember(key, result)
                    GEO_CACHE.labels("l1").inc()
                    return result
                except (TypeError, ValueError, KeyError):
                    await self.redis.delete(f"geo:{key}")
        except (RedisError, OSError):
            redis_failed = True
        if redis_failed and key in self._lru:
            self._lru.move_to_end(key)
            GEO_CACHE.labels("lru").inc()
            return self._lru[key]
        row = await self.session.scalar(select(GeocodeCache).where(GeocodeCache.query_hash == key))
        if row is not None:
            row.hit_count += 1
            result = GeoResult(
                lat=row.lat,
                lon=row.lon,
                address_norm=row.address_norm or row.query,
            )
            await self._write_l1(key, result)
            GEO_CACHE.labels("l2").inc()
            return result
        GEO_CACHE.labels("miss").inc()
        return None

    async def fetch_and_store(self, address: str) -> GeoOutcome:
        if not await self.breaker.allow():
            return GeoOutcome(GeoOutcomeStatus.BREAKER_OPEN)
        try:
            result = await self.client.search(address)
        except GeocoderUnavailable:
            await self.breaker.record_failure()
            GEOCODER_REQUESTS.labels("error").inc()
            return GeoOutcome(GeoOutcomeStatus.UNAVAILABLE)
        except GeocoderError:
            GEOCODER_REQUESTS.labels("error").inc()
            raise
        await self.breaker.record_success()
        if result is None:
            GEOCODER_REQUESTS.labels("not_found").inc()
            return GeoOutcome(GeoOutcomeStatus.NOT_FOUND)
        key = address_hash(address)
        statement = insert(GeocodeCache).values(
            query_hash=key,
            query=normalize_address(address),
            address_norm=result.address_norm,
            lat=result.lat,
            lon=result.lon,
        )
        await self.session.execute(
            statement.on_conflict_do_update(
                index_elements=[GeocodeCache.query_hash],
                set_={
                    "address_norm": result.address_norm,
                    "lat": result.lat,
                    "lon": result.lon,
                    "fetched_at": statement.excluded.fetched_at,
                },
            )
        )
        await self._write_l1(key, result)
        GEOCODER_REQUESTS.labels("ok").inc()
        return GeoOutcome(GeoOutcomeStatus.FOUND, result)
