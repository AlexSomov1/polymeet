import pytest
from pydantic import ValidationError

from app.core.config import DEV_JWT_SECRET, Settings


@pytest.mark.parametrize("secret", ["", "   ", DEV_JWT_SECRET])
def test_prod_requires_explicit_jwt_secret(monkeypatch: pytest.MonkeyPatch, secret: str) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("JWT_SECRET", secret)

    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings()


def test_dev_allows_default_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    assert Settings().jwt_secret == DEV_JWT_SECRET


def test_comma_separated_lists_are_parsed_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEO_RETRY_DELAYS_SEC", "2, 2 ,5")
    monkeypatch.setenv("ALLOWED_EMAIL_DOMAINS", "Edu.SPbSTU.ru,,spbstu.ru")

    settings = Settings()

    assert settings.geo_retry_delays_sec == [2, 2, 5]
    assert settings.allowed_email_domains == ["edu.spbstu.ru", "spbstu.ru"]


def test_empty_geocoder_user_agent_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEOCODER_USER_AGENT", "  ")

    with pytest.raises(ValidationError, match="GEOCODER_USER_AGENT"):
        Settings()
