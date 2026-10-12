"""Настройка OpenAPI: описания, operationId и приведение ответов-ошибок к RFC 9457."""

from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

API_DESCRIPTION = """\
API платформы офлайн-встреч студентов PolyMeet.

* Авторизация: заголовок `Authorization: Bearer <access_token>` (токены выдаёт `/auth/login`).
* Ошибки: RFC 9457, `application/problem+json`; клиент различает их по полю `code`.
  Ошибки валидации — 400 `VALIDATION_ERROR` с разбором по полям в `errors`.
* Списки: курсорная пагинация, `{items, next_cursor}`; следующая страница — `?cursor=<next_cursor>`.
* Время: ISO 8601 со смещением; идентификаторы — целые числа.
* Целевое время ответа (p95) указано в описании каждой операции.
"""

OPENAPI_TAGS = [
    {"name": "auth", "description": "Регистрация, вход, обновление и отзыв токенов"},
    {"name": "users", "description": "Профили, мои встречи и мои заявки"},
    {"name": "categories", "description": "Справочник категорий встреч"},
    {"name": "meetings", "description": "Лента, карта, создание и правка встреч"},
    {"name": "applications", "description": "Заявки на участие и решения организатора"},
    {"name": "health", "description": "Проверки живости и готовности"},
]

_DEFAULT_VALIDATION_SCHEMAS = ("HTTPValidationError", "ValidationError")


def operation_id(route: APIRoute) -> str:
    """operationId — имя функции роута: ``list_meetings``, ``create_meeting``."""
    return route.name


def _drop_default_validation_responses(schema: dict[str, Any]) -> None:
    # FastAPI сам добавляет 422 с HTTPValidationError, а API отвечает 400 VALIDATION_ERROR.
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            responses = operation.get("responses", {})
            response = responses.get("422")
            if response and "HTTPValidationError" in str(response.get("content")):
                del responses["422"]
    components = schema.get("components", {}).get("schemas", {})
    for name in _DEFAULT_VALIDATION_SCHEMAS:
        components.pop(name, None)


def _use_problem_json(schema: dict[str, Any]) -> None:
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            for status, response in operation.get("responses", {}).items():
                content = response.get("content", {})
                if status.isdigit() and int(status) >= 400 and "application/json" in content:
                    content["application/problem+json"] = content.pop("application/json")


def install_openapi(app: FastAPI) -> None:
    generate = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is not None:
            return app.openapi_schema
        schema = generate()  # FastAPI кэширует этот же объект в app.openapi_schema
        _drop_default_validation_responses(schema)
        _use_problem_json(schema)
        return schema

    app.openapi = openapi  # type: ignore[method-assign]
