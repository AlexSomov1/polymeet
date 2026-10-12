from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.schemas.common import Page
from app.schemas.enums import ApplicationStatus, MeetingStatus


class ApplicationCreate(BaseModel):
    message: Annotated[str, Field(max_length=300)] | None = Field(
        default=None, description="Сообщение организатору"
    )


class DecisionIn(BaseModel):
    decision: Literal["accepted", "rejected"]


class ApplicantOut(BaseModel):
    id: int
    display_name: str
    attendance_rate: float | None
    attended_count: int


class ApplicationOut(BaseModel):
    id: int
    meeting_id: int
    status: ApplicationStatus
    message: str | None
    created_at: datetime
    decided_at: datetime | None
    user: ApplicantOut


class MeetingBrief(BaseModel):
    id: int
    title: str
    starts_at: datetime
    status: MeetingStatus
    accepted_count: int
    capacity: int


class MyApplicationItem(BaseModel):
    id: int
    status: ApplicationStatus
    message: str | None
    created_at: datetime
    decided_at: datetime | None
    meeting: MeetingBrief


class ApplicationPage(Page[ApplicationOut]):
    pass


class MyApplicationPage(Page[MyApplicationItem]):
    pass
