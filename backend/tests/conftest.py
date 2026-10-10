from typing import Any

import pytest

from app.core.config import Settings

TEST_JWT_SECRET = "test-only-jwt-secret-0123456789abcdef"


def make_settings(**overrides: Any) -> Settings:
    """Настройки для тестов: быстрый Argon2 и отдельный секрет JWT."""
    values: dict[str, Any] = {
        "app_env": "test",
        "jwt_secret": TEST_JWT_SECRET,
        "argon2_time_cost": 1,
        "argon2_memory_cost": 8,
        "argon2_parallelism": 1,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Переопределяется в tests/integration/conftest.py адресами настоящих БД и Redis."""
    return make_settings()
