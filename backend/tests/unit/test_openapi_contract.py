from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from app.api.openapi import render_openapi
from app.main import create_app
from tests.api_operations import OPERATIONS, Operation
from tests.conftest import make_settings

OPENAPI_FILE = Path(__file__).resolve().parents[2] / "openapi.json"


@pytest.fixture(scope="module")
def spec() -> dict[str, Any]:
    return create_app(make_settings()).openapi()


def _operations(spec: dict[str, Any]) -> dict[str, tuple[str, str, dict[str, Any]]]:
    return {
        operation["operationId"]: (method.upper(), path, operation)
        for path, item in spec["paths"].items()
        for method, operation in item.items()
    }


def test_committed_openapi_matches_application() -> None:
    expected = render_openapi(create_app(make_settings()))

    assert OPENAPI_FILE.read_text(encoding="utf-8") == expected, (
        "backend/openapi.json устарел: выполните `python scripts/export_openapi.py` "
        "в каталоге backend и закоммитьте файл"
    )


def test_operation_ids_are_unique(spec: dict[str, Any]) -> None:
    ids = Counter(
        operation["operationId"] for item in spec["paths"].values() for operation in item.values()
    )

    assert [op_id for op_id, count in ids.items() if count > 1] == []


def test_contract_contains_exactly_the_listed_operations(spec: dict[str, Any]) -> None:
    api = {
        op_id: (method, path)
        for op_id, (method, path, _) in _operations(spec).items()
        if path.startswith("/api/v1/")
    }

    assert api == {op.operation_id: (op.method, op.path) for op in OPERATIONS}


@pytest.mark.parametrize("op", OPERATIONS, ids=lambda op: op.operation_id)
def test_openapi_security_matches_access(spec: dict[str, Any], op: Operation) -> None:
    _, _, operation = _operations(spec)[op.operation_id]
    expected = {
        "none": None,
        "optional": [{"HTTPBearer": []}, {}],
        "required": [{"HTTPBearer": []}],
    }[op.access]

    assert operation.get("security") == expected


def test_errors_are_documented_as_problem_json(spec: dict[str, Any]) -> None:
    for op_id, (_, _, operation) in _operations(spec).items():
        for status, response in operation["responses"].items():
            if int(status) >= 400:
                assert list(response["content"]) == ["application/problem+json"], op_id
                schema = response["content"]["application/problem+json"]["schema"]
                assert schema == {"$ref": "#/components/schemas/ProblemDetails"}, op_id
    assert "HTTPValidationError" not in spec["components"]["schemas"]
