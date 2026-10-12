from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import OPTIONAL_AUTH, CurrentUser, OptionalUser
from app.api.errors import (
    NotFoundError,
    NotImplementedAppError,
    UnauthorizedError,
    ValidationAppError,
    error_responses,
)
from app.api.v1.params import Cursor, PageLimit, UserId, p95
from app.schemas.applications import MyApplicationPage
from app.schemas.enums import ApplicationStatus
from app.schemas.meetings import MeetingPage
from app.schemas.users import PublicUserOut, UserOut

router = APIRouter(prefix="/users", tags=["users"])

# Маршруты /users/me... объявлены раньше /users/{user_id}, иначе их перехватит параметр.


@router.get(
    "/me",
    summary="Мой профиль",
    description=p95(150),
    responses=error_responses(UnauthorizedError, NotImplementedAppError),
)
async def get_me(user: CurrentUser) -> UserOut:
    raise NotImplementedAppError()


@router.get(
    "/me/meetings",
    summary="Мои встречи",
    description=p95(200, "Встречи, где я организатор, во всех статусах; новые сначала."),
    responses=error_responses(ValidationAppError, UnauthorizedError, NotImplementedAppError),
)
async def list_my_meetings(
    user: CurrentUser, cursor: Cursor = None, limit: PageLimit = 20
) -> MeetingPage:
    raise NotImplementedAppError()


@router.get(
    "/me/applications",
    summary="Мои заявки",
    description=p95(200, "Мои заявки с краткой информацией о встрече; новые сначала."),
    responses=error_responses(ValidationAppError, UnauthorizedError, NotImplementedAppError),
)
async def list_my_applications(
    user: CurrentUser,
    status: Annotated[ApplicationStatus | None, Query(description="Фильтр по статусу")] = None,
    cursor: Cursor = None,
    limit: PageLimit = 20,
) -> MyApplicationPage:
    raise NotImplementedAppError()


@router.get(
    "/{user_id}",
    summary="Публичный профиль",
    description=p95(150),
    openapi_extra=OPTIONAL_AUTH,
    responses=error_responses(
        ValidationAppError, UnauthorizedError, NotFoundError, NotImplementedAppError
    ),
)
async def get_user(user_id: UserId, viewer: OptionalUser) -> PublicUserOut:
    raise NotImplementedAppError()
