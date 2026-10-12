from typing import Annotated

from pydantic import BaseModel, Field

from app.schemas.enums import ErrorCode

Email = Annotated[
    str,
    Field(
        min_length=3,
        max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        json_schema_extra={"format": "email"},
        examples=["student@edu.spbstu.ru"],
    ),
]


class FieldError(BaseModel):
    field: str = Field(description="Поле запроса: `email`, `limit`, `lat` и т. п.")
    message: str


class ProblemDetails(BaseModel):
    """Ошибка в формате RFC 9457 (`application/problem+json`).

    Клиент различает ошибки по `code`; `detail` — текст для пользователя.
    """

    type: str = Field(default="about:blank", description="Всегда `about:blank`")
    title: str = Field(description="Текст HTTP-статуса", examples=["Bad Request"])
    status: int = Field(description="HTTP-статус ответа", examples=[400])
    detail: str = Field(examples=["Некорректные данные запроса"])
    instance: str | None = Field(default=None, description="Путь запроса")
    code: ErrorCode
    errors: list[FieldError] | None = Field(
        default=None, description="Ошибки по полям; только для `VALIDATION_ERROR`"
    )


class Page[ItemT](BaseModel):
    """Страница курсорной пагинации."""

    items: list[ItemT]
    next_cursor: str | None = Field(
        description="Курсор следующей страницы; `null`, если страниц больше нет"
    )
