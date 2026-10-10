from functools import lru_cache
from typing import Annotated, Any, Literal, Self

from argon2.profiles import RFC_9106_LOW_MEMORY
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEV_JWT_SECRET = "dev-only-jwt-secret-change-me-in-production"


def _split_csv(value: Any) -> Any:
    """Разбирает список из переменной окружения вида ``a,b,c``."""
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    """Все параметры приложения; значения по умолчанию рабочие для Docker Compose."""

    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    app_env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    app_timezone: str = "Europe/Moscow"

    database_url: str = "postgresql+asyncpg://polymeet:polymeet@db:5432/polymeet"
    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str = DEV_JWT_SECRET
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 30

    argon2_time_cost: int = RFC_9106_LOW_MEMORY.time_cost
    argon2_memory_cost: int = RFC_9106_LOW_MEMORY.memory_cost
    argon2_parallelism: int = RFC_9106_LOW_MEMORY.parallelism

    auth_rate_limit_attempts: int = 5
    auth_rate_limit_window_sec: int = 900
    allowed_email_domains: Annotated[list[str], NoDecode] = []

    geocoder_base_url: str = "https://nominatim.openstreetmap.org"
    geocoder_user_agent: str = "PolyMeet/1.0 (course project)"
    geocoder_rps: float = 1
    geocoder_timeout_sec: float = 1.5
    geocoder_retries: int = 2
    geo_cache_ttl_days: int = 30
    geo_retry_delays_sec: Annotated[list[int], NoDecode] = [300, 900, 3600]

    cb_fail_max: int = 5
    cb_open_seconds: int = 60
    cb_window_sec: int = 30
    cb_window_min_calls: int = 10
    cb_window_fail_rate: float = 0.5

    feed_cache_ttl_sec: int = 30

    @field_validator("allowed_email_domains", mode="before")
    @classmethod
    def _parse_domains(cls, value: Any) -> Any:
        parsed = _split_csv(value)
        if isinstance(parsed, list):
            return [str(domain).lower() for domain in parsed]
        return parsed

    @field_validator("geo_retry_delays_sec", mode="before")
    @classmethod
    def _parse_retry_delays(cls, value: Any) -> Any:
        return _split_csv(value)

    @field_validator("geocoder_user_agent")
    @classmethod
    def _require_user_agent(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GEOCODER_USER_AGENT не может быть пустым")
        return value

    @model_validator(mode="after")
    def _check_prod_secret(self) -> Self:
        if self.app_env == "prod" and self.jwt_secret.strip() in ("", DEV_JWT_SECRET):
            raise ValueError("в prod JWT_SECRET должен быть задан явно")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
