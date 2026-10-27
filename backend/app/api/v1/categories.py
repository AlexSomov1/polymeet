from fastapi import APIRouter

from app.api.v1.meetings import MeetingServiceDep
from app.api.v1.params import p95
from app.schemas.categories import CategoryOut

router = APIRouter(tags=["categories"])


@router.get(
    "/categories",
    summary="Категории встреч",
    description=p95(150),
)
async def list_categories(service: MeetingServiceDep) -> list[CategoryOut]:
    return [CategoryOut.model_validate(category) for category in await service.list_categories()]
