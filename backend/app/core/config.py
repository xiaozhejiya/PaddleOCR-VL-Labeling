from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    app_env: str = Field(default="dev", validation_alias="APP_ENV")
    app_name: str = Field(
        default="document-annotation-platform",
        validation_alias="APP_NAME",
    )
    api_prefix: str = Field(default="/api/v1", validation_alias="API_PREFIX")

    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    migrator_database_url: str | None = Field(
        default=None,
        validation_alias="MIGRATOR_DATABASE_URL",
    )
    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")
    celery_broker_url: str | None = Field(
        default=None,
        validation_alias="CELERY_BROKER_URL",
    )
    celery_result_backend: str | None = Field(
        default=None,
        validation_alias="CELERY_RESULT_BACKEND",
    )

    storage_root: Path = Field(
        default=Path("E:/code/python/K12/data"),
        validation_alias="STORAGE_ROOT",
    )
    max_upload_mb: int = Field(default=200, validation_alias="MAX_UPLOAD_MB")
    auto_migrate_on_startup: bool = Field(
        default=False,
        validation_alias="AUTO_MIGRATE_ON_STARTUP",
    )

    jwt_secret_key: str | None = Field(default=None, validation_alias="JWT_SECRET_KEY")
    jwt_expire_minutes: int = Field(
        default=1440,
        validation_alias="JWT_EXPIRE_MINUTES",
    )
    auth_cookie_name: str = Field(
        default="k12_access_token",
        validation_alias="AUTH_COOKIE_NAME",
    )
    auth_cookie_secure: bool = Field(
        default=False,
        validation_alias="AUTH_COOKIE_SECURE",
    )
    auth_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax",
        validation_alias="AUTH_COOKIE_SAMESITE",
    )

    paddleocr_vl_enabled: bool = Field(
        default=False,
        validation_alias="PADDLEOCR_VL_ENABLED",
    )

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def is_missing_or_placeholder(value: str | None) -> bool:
    if value is None or value.strip() == "":
        return True
    return "<REPLACE_WITH_" in value
