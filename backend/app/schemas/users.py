from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: int = Field(description="Роль: 0 — обычный пользователь")
    attended_count: int = Field(description="На скольких отмеченных встречах участник был")
    marked_count: int = Field(description="На скольких встречах ему отмечали явку")
    attendance_rate: float | None = Field(
        description="Надёжность: attended_count / marked_count; `null`, пока отметок нет"
    )
    created_at: datetime


class PublicUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    attended_count: int
    marked_count: int
    attendance_rate: float | None
