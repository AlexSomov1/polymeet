from fastapi import APIRouter

from app.api.errors import NotImplementedAppError, error_responses
from app.api.v1.params import p95
from app.schemas.categories import CategoryOut

router = APIRouter(tags=["categories"])


@router.get(
    "/categories",
    summary="Категории встреч",
    description=p95(150),
    responses=error_responses(NotImplementedAppError),
)
async def list_categories() -> list[CategoryOut]:
    raise NotImplementedAppError()
