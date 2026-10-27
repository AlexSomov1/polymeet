from typing import Protocol

from app.models.meeting import Meeting


class GeocodingPort(Protocol):
    async def resolve_cached(self, meeting: Meeting) -> bool:
        """Fill cached coordinates before commit; return whether a cache hit occurred."""
        ...

    async def enqueue(self, meeting_id: int) -> None:
        """Queue geocoding after the meeting has been committed."""
        ...


class NullGeocoding:
    """S06 placeholder, replaced by the real geocoder in S09."""

    async def resolve_cached(self, meeting: Meeting) -> bool:
        return False

    async def enqueue(self, meeting_id: int) -> None:
        return None
