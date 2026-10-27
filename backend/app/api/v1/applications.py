from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, SessionDep
from app.api.errors import (
    AlreadyAppliedError,
    CapacityReachedError,
    ForbiddenError,
    InvalidTransitionError,
    MeetingNotPublishedError,
    NotFoundError,
    UnauthorizedError,
    ValidationAppError,
    error_responses,
)
from app.api.v1.mappers import to_application_out
from app.api.v1.params import ApplicationId, Cursor, MeetingId, PageLimit, p95
from app.models import enums as model_enums
from app.schemas.applications import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationPage,
    DecisionIn,
)
from app.schemas.enums import ApplicationStatus
from app.services.application_service import ApplicationService

router = APIRouter(tags=["applications"])


def get_application_service(session: SessionDep) -> ApplicationService:
    return ApplicationService(session)


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]


def to_model_status(status: ApplicationStatus | None) -> model_enums.ApplicationStatus | None:
    return model_enums.ApplicationStatus[status.name] if status is not None else None


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
    ),
)
async def apply_to_meeting(
    meeting_id: MeetingId,
    user: CurrentUser,
    service: ApplicationServiceDep,
    payload: ApplicationCreate | None = None,
) -> ApplicationOut:
    message = payload.message if payload is not None else None
    return to_application_out(await service.apply(user, meeting_id, message))


@router.get(
    "/meetings/{meeting_id}/applications",
    summary="Заявки на мою встречу",
    description=p95(200, "Только организатор. Очередь в порядке подачи."),
    responses=error_responses(ValidationAppError, UnauthorizedError, ForbiddenError, NotFoundError),
)
async def list_meeting_applications(
    meeting_id: MeetingId,
    user: CurrentUser,
    service: ApplicationServiceDep,
    status: Annotated[ApplicationStatus | None, Query(description="Фильтр по статусу")] = None,
    cursor: Cursor = None,
    limit: PageLimit = 20,
) -> ApplicationPage:
    applications, next_cursor = await service.list_for_organizer(
        user, meeting_id, to_model_status(status), cursor, limit
    )
    return ApplicationPage(
        items=[to_application_out(application) for application in applications],
        next_cursor=next_cursor,
    )


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
    ),
)
async def withdraw_my_application(
    meeting_id: MeetingId, user: CurrentUser, service: ApplicationServiceDep
) -> None:
    await service.withdraw(user, meeting_id)


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
    ),
)
async def decide_application(
    application_id: ApplicationId,
    payload: DecisionIn,
    user: CurrentUser,
    service: ApplicationServiceDep,
) -> ApplicationOut:
    decision = model_enums.ApplicationStatus[payload.decision.upper()]
    return to_application_out(await service.decide(user, application_id, decision))
