"""Ошибки API: иерархия ``AppError`` и обработчики, приводящие всё к RFC 9457.

Сами классы ошибок определены в ``app.core.errors``, чтобы сервисы могли поднимать их,
не завися от слоя API; здесь они реэкспортируются.
"""

from collections.abc import Mapping
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import (
    PROBLEM_JSON,
    AlreadyAppliedError,
    AppError,
    CapacityReachedError,
    DependencyUnavailableError,
    EmailTakenError,
    ErrorDetails,
    ForbiddenError,
    InternalError,
    InvalidCredentialsError,
    InvalidTransitionError,
    MeetingNotPublishedError,
    NotFoundError,
    NotImplementedAppError,
    RateLimitedError,
    UnauthorizedError,
    ValidationAppError,
    problem_details,
)
from app.schemas.common import ProblemDetails

__all__ = [
    "AlreadyAppliedError",
    "AppError",
    "CapacityReachedError",
    "DependencyUnavailableError",
    "EmailTakenError",
    "ForbiddenError",
    "InternalError",
    "InvalidCredentialsError",
    "InvalidTransitionError",
    "MeetingNotPublishedError",
    "NotFoundError",
    "NotImplementedAppError",
    "RateLimitedError",
    "UnauthorizedError",
    "ValidationAppError",
    "error_responses",
    "register_error_handlers",
]

logger = structlog.get_logger(__name__)

_LOCATION_PREFIXES = {"body", "query", "path", "header", "cookie"}

_CODES_BY_STATUS = {
    400: ValidationAppError.code,
    401: UnauthorizedError.code,
    403: ForbiddenError.code,
    404: NotFoundError.code,
    405: "METHOD_NOT_ALLOWED",
    429: RateLimitedError.code,
    503: DependencyUnavailableError.code,
}


def error_responses(*errors: type[AppError]) -> dict[int | str, dict[str, Any]]:
    """Описание ошибок для ``responses=`` роута: по статусу, со списком возможных кодов."""
    by_status: dict[int, list[type[AppError]]] = {}
    for error in errors:
        by_status.setdefault(error.http_status, []).append(error)
    return {
        status: {
            "model": ProblemDetails,
            "description": "; ".join(f"`{e.code}` — {e.default_message}" for e in group),
        }
        for status, group in sorted(by_status.items())
    }


def _problem_response(
    request: Request,
    status: int,
    code: str,
    detail: str,
    errors: ErrorDetails | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body = problem_details(
        status=status, code=code, detail=detail, instance=request.url.path, errors=errors
    )
    return JSONResponse(body, status_code=status, headers=headers, media_type=PROBLEM_JSON)


async def _handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return _problem_response(
        request, exc.http_status, exc.code, exc.message, exc.details, exc.headers
    )


def _field_name(location: tuple[Any, ...]) -> str:
    parts = location[1:] if len(location) > 1 and location[0] in _LOCATION_PREFIXES else location
    return ".".join(str(part) for part in parts)


async def _handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"field": _field_name(tuple(error.get("loc", ()))), "message": str(error.get("msg", ""))}
        for error in exc.errors()
    ]
    return _problem_response(
        request, 400, ValidationAppError.code, ValidationAppError.default_message, errors
    )


async def _handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    status = exc.status_code
    code = _CODES_BY_STATUS.get(status, InternalError.code if status >= 500 else "HTTP_ERROR")
    detail = exc.detail if isinstance(exc.detail, str) else code
    return _problem_response(request, status, code, detail, headers=exc.headers)


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # Обычно сюда не доходит: RequestContextMiddleware сам отвечает 500 и пишет http_error.
    logger.error("unhandled_exception", exc_info=exc)
    return _problem_response(request, 500, InternalError.code, InternalError.default_message)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected_error)
