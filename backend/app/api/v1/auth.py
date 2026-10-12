from fastapi import APIRouter

from app.api.errors import (
    DependencyUnavailableError,
    EmailTakenError,
    InvalidCredentialsError,
    NotImplementedAppError,
    RateLimitedError,
    UnauthorizedError,
    ValidationAppError,
    error_responses,
)
from app.api.v1.params import p95
from app.schemas.auth import AuthResponse, LoginIn, RefreshIn, RegisterIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=201,
    summary="Регистрация",
    description=p95(500, "Создаёт пользователя и сразу выдаёт пару токенов."),
    responses=error_responses(ValidationAppError, EmailTakenError, NotImplementedAppError),
)
async def register(payload: RegisterIn) -> AuthResponse:
    raise NotImplementedAppError()


@router.post(
    "/login",
    summary="Вход",
    description=p95(
        500,
        "Неверный пароль и несуществующий e-mail дают одинаковый ответ. "
        "После 5 неудачных попыток с одного IP — 429 с заголовком `Retry-After`.",
    ),
    responses=error_responses(
        ValidationAppError, InvalidCredentialsError, RateLimitedError, NotImplementedAppError
    ),
)
async def login(payload: LoginIn) -> AuthResponse:
    raise NotImplementedAppError()


@router.post(
    "/refresh",
    summary="Обновление токенов",
    description=p95(
        500,
        "Ротация: старый refresh-токен отзывается, выдаётся новая пара. "
        "Повторное использование старого токена — 401.",
    ),
    responses=error_responses(
        ValidationAppError, UnauthorizedError, DependencyUnavailableError, NotImplementedAppError
    ),
)
async def refresh(payload: RefreshIn) -> AuthResponse:
    raise NotImplementedAppError()


@router.post(
    "/logout",
    status_code=204,
    summary="Выход",
    description=p95(500, "Отзывает переданный refresh-токен."),
    responses=error_responses(
        ValidationAppError, UnauthorizedError, DependencyUnavailableError, NotImplementedAppError
    ),
)
async def logout(payload: RefreshIn) -> None:
    raise NotImplementedAppError()
