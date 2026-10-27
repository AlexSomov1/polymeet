"""Лента встреч и встречи на карте: проверка параметров, курсор."""

from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationAppError
from app.core.pagination import decode_cursor, encode_cursor
from app.models.meeting import Meeting
from app.repositories.category_repository import CategoryRepository
from app.repositories.meeting_repository import BBox, FeedFilters, GeoCircle, MeetingRepository
from app.schemas.meetings import MeetingListItem, MeetingPage

ItemBuilder = Callable[[Meeting, float | None], MeetingListItem]

_POINT_FIELDS = ("lat", "lon", "radius_km")


def geo_circle(lat: float | None, lon: float | None, radius_km: float | None) -> GeoCircle | None:
    """Круг поиска; ``lat``, ``lon`` и ``radius_km`` задаются только все вместе."""
    values = {"lat": lat, "lon": lon, "radius_km": radius_km}
    missing = [name for name in _POINT_FIELDS if values[name] is None]
    if len(missing) == len(_POINT_FIELDS):
        return None
    if missing:
        raise ValidationAppError(
            details=[
                {"field": name, "message": "lat, lon и radius_km задаются только вместе"}
                for name in missing
            ]
        )
    assert lat is not None and lon is not None and radius_km is not None
    return GeoCircle(lat=lat, lon=lon, radius_m=radius_km * 1000)


def parse_bbox(value: str) -> BBox:
    """Видимая область ``min_lon,min_lat,max_lon,max_lat``; формат уже проверен схемой."""
    try:
        min_lon, min_lat, max_lon, max_lat = (float(part) for part in value.split(","))
    except ValueError as exc:
        raise ValidationAppError.for_field(
            "bbox", "Ожидается min_lon,min_lat,max_lon,max_lat"
        ) from exc
    if not all(-180 <= lon <= 180 for lon in (min_lon, max_lon)):
        raise ValidationAppError.for_field("bbox", "Долгота должна быть от -180 до 180")
    if not all(-90 <= lat <= 90 for lat in (min_lat, max_lat)):
        raise ValidationAppError.for_field("bbox", "Широта должна быть от -90 до 90")
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValidationAppError.for_field(
            "bbox", "Минимальные границы должны быть меньше максимальных"
        )
    return BBox(min_lon=min_lon, min_lat=min_lat, max_lon=max_lon, max_lat=max_lat)


def day_bounds(day: date, timezone: str) -> tuple[datetime, datetime]:
    """Сутки ``day`` по местному времени ``timezone`` — полуинтервал в UTC."""
    zone = ZoneInfo(timezone)
    start = datetime.combine(day, time.min, tzinfo=zone)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=zone)
    return start.astimezone(UTC), end.astimezone(UTC)


def _decode_feed_cursor(cursor: str) -> tuple[datetime, int]:
    starts_at, meeting_id = decode_cursor(cursor, [datetime, int])
    if starts_at.tzinfo is None or meeting_id <= 0:
        raise ValidationAppError.for_field("cursor", "Недействительный курсор")
    return starts_at, meeting_id


def _distance_km(distance_m: float | None) -> float | None:
    return round(distance_m / 1000, 1) if distance_m is not None else None


class FeedService:
    def __init__(self, session: AsyncSession, timezone: str) -> None:
        self._meetings = MeetingRepository(session)
        self._categories = CategoryRepository(session)
        self._timezone = timezone

    async def _filters(
        self, category: str | None, day: date | None, has_free_places: bool
    ) -> FeedFilters | None:
        """Общие условия ленты и карты; ``None`` — неизвестная категория, выдача пуста."""
        category_id = None
        if category is not None:
            found = await self._categories.get_by_slug(category)
            if found is None:
                return None
            category_id = found.id
        return FeedFilters(
            starts_after=datetime.now(UTC),
            category_id=category_id,
            starts_between=day_bounds(day, self._timezone) if day is not None else None,
            has_free_places=has_free_places,
        )

    async def _feed_page(
        self,
        *,
        category: str | None,
        day: date | None,
        has_free_places: bool,
        q: str | None,
        circle: GeoCircle | None,
        after: tuple[datetime, int] | None,
        limit: int,
        build_item: ItemBuilder,
    ) -> MeetingPage:
        filters = await self._filters(category, day, has_free_places)
        if filters is None:
            return MeetingPage(items=[], next_cursor=None)
        filters = replace(filters, query=q, circle=circle)
        rows = await self._meetings.list_feed(filters, after, limit)
        items = rows[:limit]
        next_cursor = None
        if len(rows) > limit:
            last = items[-1][0]
            next_cursor = encode_cursor([last.starts_at, last.id])
        return MeetingPage(
            items=[build_item(meeting, _distance_km(distance)) for meeting, distance in items],
            next_cursor=next_cursor,
        )

    async def list_feed(
        self,
        *,
        category: str | None,
        day: date | None,
        lat: float | None,
        lon: float | None,
        radius_km: float | None,
        has_free_places: bool,
        q: str | None,
        cursor: str | None,
        limit: int,
        build_item: ItemBuilder,
    ) -> MeetingPage:
        circle = geo_circle(lat, lon, radius_km)
        after = _decode_feed_cursor(cursor) if cursor is not None else None

        return await self._feed_page(
            category=category,
            day=day,
            has_free_places=has_free_places,
            q=q,
            circle=circle,
            after=after,
            limit=limit,
            build_item=build_item,
        )

    async def list_on_map(
        self,
        *,
        bbox: str,
        category: str | None,
        day: date | None,
        has_free_places: bool,
        limit: int,
        build_item: ItemBuilder,
    ) -> list[MeetingListItem]:
        area = parse_bbox(bbox)
        filters = await self._filters(category, day, has_free_places)
        if filters is None:
            return []
        meetings = await self._meetings.list_in_bbox(filters, area, limit)
        return [build_item(meeting, None) for meeting in meetings]
