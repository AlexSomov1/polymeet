from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import Page
from app.schemas.enums import ApplicationStatus, GeoStatus, MeetingStatus

CategorySlug = Annotated[
    str,
    Field(
        min_length=1,
        max_length=32,
        pattern=r"^[a-z0-9_-]+$",
        description="slug категории из `GET /categories`",
        examples=["games"],
    ),
]
Title = Annotated[str, Field(min_length=3, max_length=120, examples=["Настолки в «Кубе»"])]
Description = Annotated[str, Field(max_length=2000)]
Duration = Annotated[int, Field(ge=15, le=720, description="Длительность, минуты")]
Address = Annotated[
    str,
    Field(min_length=3, max_length=300, examples=["Санкт-Петербург, Политехническая ул., 29"]),
]
AddressHint = Annotated[
    str, Field(max_length=200, description="Как найти место", examples=["вход со двора"])
]
Capacity = Annotated[int, Field(ge=2, le=100, description="Лимит участников")]
Latitude = Annotated[float, Field(ge=-90, le=90)]
Longitude = Annotated[float, Field(ge=-180, le=180)]


class MeetingCreate(BaseModel):
    title: Title
    description: Description = ""
    category: CategorySlug
    starts_at: AwareDatetime = Field(description="Начало встречи, в будущем, со смещением")
    duration_minutes: Duration
    address: Address
    address_hint: AddressHint | None = None
    capacity: Capacity
    auto_accept: bool = Field(default=False, description="Принимать заявки без решения")


_PATCH_NON_NULLABLE = (
    "title",
    "description",
    "category",
    "starts_at",
    "duration_minutes",
    "address",
    "capacity",
    "auto_accept",
    "status",
)


def _hide_null_in_schema(schema: dict[str, Any]) -> None:
    # В коде поля nullable (None = «не передано»), но в контракте null для них запрещён
    for name in _PATCH_NON_NULLABLE:
        prop = schema["properties"][name]
        variants = [v for v in prop.pop("anyOf") if v != {"type": "null"}]
        prop.pop("default", None)
        prop.update(variants[0])


class MeetingUpdate(BaseModel):
    """Частичное изменение: передаются только меняемые поля.

    `null` допустим только для `address_hint`. Смена `address` сбрасывает координаты,
    встреча снова геокодируется. `status` публикует или отменяет встречу.
    Сервис берёт изменения через ``model_dump(exclude_unset=True)``.
    """

    model_config = ConfigDict(json_schema_extra=_hide_null_in_schema)

    title: Title | None = None
    description: Description | None = None
    category: CategorySlug | None = None
    starts_at: AwareDatetime | None = None
    duration_minutes: Duration | None = None
    address: Address | None = None
    address_hint: AddressHint | None = None
    capacity: Capacity | None = None
    auto_accept: bool | None = None
    status: Literal["published", "cancelled"] | None = None

    @field_validator(*_PATCH_NON_NULLABLE)
    @classmethod
    def _reject_explicit_null(cls, value: object) -> object:
        # Срабатывает только на переданные поля: отсутствие поля — это «не менять»
        if value is None:
            raise ValueError("поле не может быть null")
        return value


class LocationIn(BaseModel):
    lat: Latitude
    lon: Longitude


class OrganizerBrief(BaseModel):
    id: int
    display_name: str


class OrganizerOut(BaseModel):
    id: int
    display_name: str
    attendance_rate: float | None


class MyApplicationOut(BaseModel):
    id: int
    status: ApplicationStatus


class MeetingListItem(BaseModel):
    id: int
    status: MeetingStatus
    geo_status: GeoStatus
    title: str
    category: str = Field(description="slug категории")
    starts_at: datetime
    duration_minutes: int
    address: str
    lat: float | None = Field(description="`null`, пока адрес не геокодирован")
    lon: float | None
    capacity: int
    accepted_count: int
    free_places: int
    organizer: OrganizerBrief
    distance_km: float | None = Field(
        description="Расстояние до точки из запроса, км; `null`, если точка не задана"
    )


class MeetingOut(BaseModel):
    id: int
    status: MeetingStatus
    geo_status: GeoStatus
    title: str
    description: str
    category: str = Field(description="slug категории")
    starts_at: datetime
    duration_minutes: int
    address: str
    address_hint: str | None
    address_norm: str | None = Field(description="Адрес, как его понял геокодер")
    lat: float | None
    lon: float | None
    capacity: int
    accepted_count: int
    free_places: int
    auto_accept: bool
    organizer: OrganizerOut
    my_application: MyApplicationOut | None = Field(
        description="Заявка текущего пользователя; `null` без авторизации или без заявки"
    )
    created_at: datetime


class MeetingPage(Page[MeetingListItem]):
    pass
