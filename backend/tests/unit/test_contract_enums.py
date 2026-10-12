from enum import IntEnum, StrEnum

import pytest

from app.core import errors
from app.models import enums as db_enums
from app.schemas import enums as api_enums


@pytest.mark.parametrize("name", ["MeetingStatus", "GeoStatus", "ApplicationStatus"])
def test_api_enum_mirrors_database_enum(name: str) -> None:
    db_enum: type[IntEnum] = getattr(db_enums, name)
    api_enum: type[StrEnum] = getattr(api_enums, name)

    assert {member.name for member in api_enum} == {member.name for member in db_enum}
    assert all(member.value == member.name.lower() for member in api_enum)


def _all_subclasses(cls: type) -> set[type]:
    found = set(cls.__subclasses__())
    for sub in list(found):
        found |= _all_subclasses(sub)
    return found


def test_every_application_error_code_is_in_contract() -> None:
    codes = {error.code for error in _all_subclasses(errors.AppError)}

    assert codes <= {code.value for code in api_enums.ErrorCode}


def test_each_error_class_has_its_own_code() -> None:
    # InternalError — явное имя для базового INTERNAL_ERROR, остальные коды уникальны
    classes = _all_subclasses(errors.AppError) - {errors.InternalError}
    codes = [cls.code for cls in classes]

    assert len(codes) == len(set(codes))
    assert errors.AppError.code not in codes
