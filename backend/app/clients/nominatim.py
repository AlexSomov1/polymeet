"""Nominatim search client. Every HTTP attempt obtains its own rate-limit slot."""

import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx

from app.core.config import Settings
from app.core.slot_limiter import SlotLimiter, SlotLimitTimeout


class GeocoderUnavailable(Exception):
    """A transient failure that may be retried."""


class GeocoderError(Exception):
    """A permanent request or response error."""


@dataclass(frozen=True)
class GeoResult:
    lat: float
    lon: float
    address_norm: str


class NominatimClient:
    def __init__(
        self,
        settings: Settings,
        http: httpx.AsyncClient,
        limiter: SlotLimiter,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.settings = settings
        self.http = http
        self.limiter = limiter
        self._sleep = sleep

    async def search(self, address: str) -> GeoResult | None:
        for attempt in range(self.settings.geocoder_retries + 1):
            try:
                await self.limiter.acquire("nominatim:slot", self.settings.geocoder_rps)
                response = await self.http.get(
                    f"{self.settings.geocoder_base_url.rstrip('/')}/search",
                    params={"q": address, "format": "jsonv2", "limit": 1, "accept-language": "ru"},
                    headers={"User-Agent": self.settings.geocoder_user_agent},
                    timeout=self.settings.geocoder_timeout_sec,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    raise GeocoderUnavailable(f"Nominatim HTTP {response.status_code}")
                if response.status_code >= 400:
                    raise GeocoderError(f"Nominatim HTTP {response.status_code}")
                try:
                    data = response.json()
                    if not isinstance(data, list):
                        raise ValueError("response is not a list")
                    if not data:
                        return None
                    first = data[0]
                    return GeoResult(
                        lat=float(first["lat"]),
                        lon=float(first["lon"]),
                        address_norm=str(first["display_name"]),
                    )
                except (KeyError, TypeError, ValueError, IndexError) as exc:
                    raise GeocoderError("Malformed Nominatim response") from exc
            except (httpx.TimeoutException, httpx.NetworkError, SlotLimitTimeout) as exc:
                unavailable = GeocoderUnavailable("Nominatim connection failed")
                unavailable.__cause__ = exc
            except GeocoderUnavailable as exc:
                unavailable = exc
            if attempt == self.settings.geocoder_retries:
                raise unavailable
            await self._sleep((0.3 * (2**attempt)) + random.uniform(0, 0.1))
        raise AssertionError("unreachable")
