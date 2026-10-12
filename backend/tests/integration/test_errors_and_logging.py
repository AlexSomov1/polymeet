from datetime import datetime

import httpx
import pytest
from fastapi import FastAPI
from ulid import ULID

from tests.integration.helpers import (
    AuthHeaders,
    CreateUser,
    add_probe_routes,
    read_log_records,
)


@pytest.fixture
def app(app: FastAPI) -> FastAPI:
    add_probe_routes(app)
    return app


async def test_validation_error_is_400_with_field_details(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/_probe/echo", params={"limit": 0}, json={"name": "x", "age": -1})

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    problem = response.json()
    assert (problem["status"], problem["code"]) == (400, "VALIDATION_ERROR")
    assert problem["instance"] == "/_probe/echo"
    assert {error["field"] for error in problem["errors"]} == {"limit", "name", "age"}
    assert all(error["message"] for error in problem["errors"])


async def test_unhandled_exception_is_500_without_internals(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()

    response = await client.get("/_probe/boom")

    assert response.status_code == 500
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "Внутренняя ошибка сервера",
        "instance": "/_probe/boom",
        "code": "INTERNAL_ERROR",
    }
    assert "secret internal detail" not in response.text
    assert "Traceback" not in response.text
    assert response.headers["X-Request-ID"]

    records = read_log_records(capsys)
    error_log = next(record for record in records if record["event"] == "http_error")
    assert "RuntimeError: secret internal detail" in error_log["exception"]
    request_log = next(record for record in records if record["event"] == "http_request")
    assert request_log["status"] == 500


@pytest.mark.parametrize(
    ("method", "path", "status", "code"),
    [
        ("GET", "/no-such-route", 404, "NOT_FOUND"),
        ("POST", "/health", 405, "METHOD_NOT_ALLOWED"),
    ],
)
async def test_routing_errors_use_unified_format(
    client: httpx.AsyncClient, method: str, path: str, status: int, code: str
) -> None:
    response = await client.request(method, path)

    assert response.status_code == status
    assert response.headers["content-type"] == "application/problem+json"
    assert (response.json()["status"], response.json()["code"]) == (status, code)


async def test_incoming_request_id_is_returned(client: httpx.AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "trace-42.a_b:c"})

    assert response.headers["X-Request-ID"] == "trace-42.a_b:c"


@pytest.mark.parametrize("incoming", [None, "", "has spaces", "x" * 129])
async def test_request_id_is_generated_when_missing_or_unsafe(
    client: httpx.AsyncClient, incoming: str | None
) -> None:
    headers = {} if incoming is None else {"X-Request-ID": incoming}

    response = await client.get("/health", headers=headers)

    generated = response.headers["X-Request-ID"]
    assert generated != incoming
    assert str(ULID.from_str(generated)) == generated


async def test_request_log_line_is_json_with_all_fields(
    client: httpx.AsyncClient,
    create_user: CreateUser,
    auth_headers: AuthHeaders,
    capsys: pytest.CaptureFixture[str],
) -> None:
    user = await create_user()
    capsys.readouterr()

    response = await client.get(
        "/_probe/items/42",
        headers={**auth_headers(user), "X-Request-ID": "log-check-1"},
    )

    assert response.status_code == 200
    records = read_log_records(capsys)
    [record] = [record for record in records if record["event"] == "http_request"]
    assert record["level"] == "info"
    assert datetime.fromisoformat(record["ts"]).utcoffset() is not None
    assert record["method"] == "GET"
    assert record["path"] == "/_probe/items/{item_id}"
    assert record["status"] == 200
    assert isinstance(record["duration_ms"], int)
    assert record["request_id"] == "log-check-1"
    assert record["user_id"] == user.id
    assert record["cache"] == "hit"


async def test_request_log_omits_user_for_anonymous_request(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()

    await client.get("/health")

    [record] = [r for r in read_log_records(capsys) if r["event"] == "http_request"]
    assert "user_id" not in record
    assert "cache" not in record


async def test_request_log_has_full_template_for_nested_router(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()

    await client.get("/api/v1/meetings/42")

    [record] = [r for r in read_log_records(capsys) if r["event"] == "http_request"]
    assert record["path"] == "/api/v1/meetings/{meeting_id}"
