from datetime import UTC, date, datetime

import pytest

from app.core.errors import ValidationAppError
from app.services.feed_service import day_bounds, geo_circle, parse_bbox


@pytest.mark.parametrize(
    ("lat", "lon", "radius_km", "missing"),
    [
        (60.0, None, None, {"lon", "radius_km"}),
        (None, 30.3, None, {"lat", "radius_km"}),
        (60.0, 30.3, None, {"radius_km"}),
        (None, None, 3.0, {"lat", "lon"}),
        (60.0, None, 3.0, {"lon"}),
    ],
)
def test_point_params_go_together(
    lat: float | None, lon: float | None, radius_km: float | None, missing: set[str]
) -> None:
    with pytest.raises(ValidationAppError) as error:
        geo_circle(lat, lon, radius_km)

    assert error.value.http_status == 400
    assert {item["field"] for item in error.value.details or []} == missing


def test_point_is_optional_and_radius_is_in_meters() -> None:
    assert geo_circle(None, None, None) is None
    circle = geo_circle(60.0, 30.3, 2.5)
    assert circle is not None
    assert (circle.lat, circle.lon, circle.radius_m) == (60.0, 30.3, 2500)


@pytest.mark.parametrize(
    "bbox",
    [
        "30.45,59.90,30.25,60.05",  # min_lon > max_lon
        "30.25,60.05,30.45,59.90",  # min_lat > max_lat
        "30.25,59.90,30.25,60.05",  # нулевая ширина
        "-181,59.90,30.45,60.05",
        "30.25,59.90,180.5,60.05",
        "30.25,-91,30.45,60.05",
        "30.25,59.90,30.45,90.1",
        "170,10,-170,20",  # через антимеридиан
    ],
)
def test_bbox_rejects_inverted_and_out_of_range(bbox: str) -> None:
    with pytest.raises(ValidationAppError) as error:
        parse_bbox(bbox)

    assert error.value.http_status == 400
    assert [item["field"] for item in error.value.details or []] == ["bbox"]


def test_bbox_parses_bounds() -> None:
    area = parse_bbox("-180,-90,180,90")
    assert (area.min_lon, area.min_lat, area.max_lon, area.max_lat) == (-180, -90, 180, 90)


def test_day_is_local_midnight_to_midnight_in_utc() -> None:
    start, end = day_bounds(date(2030, 10, 13), "Europe/Moscow")

    assert start == datetime(2030, 10, 12, 21, 0, tzinfo=UTC)
    assert end == datetime(2030, 10, 13, 21, 0, tzinfo=UTC)
    # 23:30 по Москве 13-го — ещё эти сутки, 00:30 14-го — уже следующие
    assert start <= datetime(2030, 10, 13, 20, 30, tzinfo=UTC) < end
    assert not datetime(2030, 10, 13, 21, 30, tzinfo=UTC) < end
