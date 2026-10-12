"""Иерархия ошибок приложения.

Модуль не зависит от FastAPI: ошибки поднимают сервисы и core, а превращает их
в HTTP-ответы ``app.api.errors``.
"""

from http import HTTPStatus
from typing import Any, ClassVar, Self

ErrorDetails = list[dict[str, Any]]

PROBLEM_JSON = "application/problem+json"


def problem_details(
    *,
    status: int,
    code: str,
    detail: str,
    instance: str | None = None,
    errors: ErrorDetails | None = None,
) -> dict[str, Any]:
    """Тело ответа об ошибке по RFC 9457 (бывший RFC 7807) с расширениями ``code`` и ``errors``.

    ``type`` всегда ``about:blank``: машиночитаемый вид ошибки передаёт ``code``.
    """
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "code": code,
    }
    if instance is not None:
        body["instance"] = instance
    if errors is not None:
        body["errors"] = errors
    return body


class AppError(Exception):
    """Ошибка с кодом API. ``details`` уходит в поле ``errors`` ответа."""

    code: ClassVar[str] = "INTERNAL_ERROR"
    http_status: ClassVar[int] = 500
    default_message: ClassVar[str] = "Внутренняя ошибка сервера"

    def __init__(
        self,
        message: str | None = None,
        details: ErrorDetails | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details
        self.headers = headers or {}
        super().__init__(self.message)


class ValidationAppError(AppError):
    code = "VALIDATION_ERROR"
    http_status = 400
    default_message = "Некорректные данные запроса"

    @classmethod
    def for_field(cls, field: str, message: str) -> Self:
        return cls(details=[{"field": field, "message": message}])


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    http_status = 401
    default_message = "Требуется авторизация"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message, headers={"WWW-Authenticate": "Bearer"})


class InvalidCredentialsError(AppError):
    code = "INVALID_CREDENTIALS"
    http_status = 401
    default_message = "Неверный e-mail или пароль"


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    http_status = 403
    default_message = "Недостаточно прав"


class NotFoundError(AppError):
    code = "NOT_FOUND"
    http_status = 404
    default_message = "Объект не найден"


class EmailTakenError(AppError):
    code = "EMAIL_TAKEN"
    http_status = 409
    default_message = "Этот e-mail уже зарегистрирован"


class AlreadyAppliedError(AppError):
    code = "ALREADY_APPLIED"
    http_status = 409
    default_message = "Заявка на эту встречу уже подана"


class CapacityReachedError(AppError):
    code = "CAPACITY_REACHED"
    http_status = 409
    default_message = "Свободных мест нет"


class InvalidTransitionError(AppError):
    code = "INVALID_TRANSITION"
    http_status = 409
    default_message = "Недопустимый переход статуса"


class MeetingNotPublishedError(AppError):
    code = "MEETING_NOT_PUBLISHED"
    http_status = 422
    default_message = "Встреча не опубликована, отменена или уже началась"


class RateLimitedError(AppError):
    code = "RATE_LIMITED"
    http_status = 429
    default_message = "Слишком много попыток, повторите позже"

    def __init__(self, retry_after: int, message: str | None = None) -> None:
        self.retry_after = max(1, retry_after)
        super().__init__(message, headers={"Retry-After": str(self.retry_after)})


class DependencyUnavailableError(AppError):
    code = "DEPENDENCY_UNAVAILABLE"
    http_status = 503
    default_message = "Сервис временно недоступен"


class InternalError(AppError):
    pass


class NotImplementedAppError(AppError):
    code = "NOT_IMPLEMENTED"
    http_status = 501
    default_message = "Эндпоинт ещё не реализован"
