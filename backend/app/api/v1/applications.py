from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser
from app.api.errors import (
    AlreadyAppliedError,
    CapacityReachedError,
    ForbiddenError,
    InvalidTransitionError,
    MeetingNotPublishedError,
    NotFoundError,
    NotImplementedAppError,
    UnauthorizedError,
    ValidationAppError,
    error_responses,
)
from app.api.v1.params import ApplicationId, Cursor, MeetingId, PageLimit, p95
from app.schemas.applications import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationPage,
    DecisionIn,
)
from app.schemas.enums import ApplicationStatus

router = APIRouter(tags=["applications"])


@router.post(
    "/meetings/{meeting_id}/applications",
    status_code=201,
    summary="Подать заявку",
    description=p95(
        300,
        "Статус новой заявки: `accepted` при автоприёме, `waitlist`, если мест нет, "
        "иначе `pending`. Повторная заявка — 409; после отзыва можно подать снова.",
    ),
    responses=error_responses(
        ValidationAppError,
        UnauthorizedError,
        ForbiddenError,
        NotFoundError,
        AlreadyAppliedError,
        MeetingNotPublishedError,
        NotImplementedAppError,
    ),
)
async def apply_to_meeting(
    meeting_id: MeetingId, user: CurrentUser, payload: ApplicationCreate | None = None
) -> ApplicationOut:
    raise NotImplementedAppError()


@router.get(
    "/meetings/{meeting_id}/applications",
    summary="Заявки на мою встречу",
    description=p95(200, "Только организатор. Очередь в порядке подачи."),
    responses=error_responses(
        ValidationAppError, UnauthorizedError, ForbiddenError, NotFoundError, NotImplementedAppError
    ),
)
async def list_meeting_applications(
    meeting_id: MeetingId,
    user: CurrentUser,
    status: Annotated[ApplicationStatus | None, Query(description="Фильтр по статусу")] = None,
    cursor: Cursor = None,
    limit: PageLimit = 20,
) -> ApplicationPage:
    raise NotImplementedAppError()


@router.delete(
    "/meetings/{meeting_id}/applications/me",
    status_code=204,
    summary="Отменить участие",
    description=p95(
        300,
        "Отзывает мою заявку (`withdrawn`). Если она была принята, место получает "
        "первый из листа ожидания.",
    ),
    responses=error_responses(
        ValidationAppError,
        UnauthorizedError,
        NotFoundError,
        InvalidTransitionError,
        NotImplementedAppError,
    ),
)
async def withdraw_my_application(meeting_id: MeetingId, user: CurrentUser) -> None:
    raise NotImplementedAppError()


@router.post(
    "/applications/{application_id}/decision",
    summary="Принять или отклонить заявку",
    description=p95(
        300,
        "Только организатор. Отказ принятой заявке освобождает место для листа ожидания.",
    ),
    responses=error_responses(
        ValidationAppError,
        UnauthorizedError,
        ForbiddenError,
        NotFoundError,
        CapacityReachedError,
        InvalidTransitionError,
        NotImplementedAppError,
    ),
)
async def decide_application(
    application_id: ApplicationId, payload: DecisionIn, user: CurrentUser
) -> ApplicationOut:
    raise NotImplementedAppError()
