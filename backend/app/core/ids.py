from ulid import ULID


def new_id() -> str:
    """Новый идентификатор: ULID, 26 символов, монотонно растёт со временем."""
    return str(ULID())
