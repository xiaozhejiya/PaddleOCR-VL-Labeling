from typing import Any

from sqlalchemy import text

from app.core.config import get_settings, is_missing_or_placeholder
from app.db.session import engine

try:
    from redis import Redis
except ModuleNotFoundError:  # pragma: no cover - 依赖缺失仅在精简测试环境出现
    Redis = None  # type: ignore[assignment]


def database_health() -> dict[str, Any]:
    settings = get_settings()
    if is_missing_or_placeholder(settings.database_url):
        return {"status": "not_configured"}
    if engine is None:
        return {"status": "not_configured"}

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_type": type(exc).__name__}


def redis_health() -> dict[str, Any]:
    settings = get_settings()
    if is_missing_or_placeholder(settings.redis_url):
        return {"status": "not_configured"}
    if Redis is None:
        return {"status": "not_installed"}

    client: Redis | None = None
    try:
        client = Redis.from_url(settings.redis_url, socket_connect_timeout=2)
        client.ping()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error_type": type(exc).__name__}
    finally:
        if client is not None:
            client.close()


def service_health() -> dict[str, Any]:
    database = database_health()
    redis = redis_health()
    overall = "ok"
    if database["status"] != "ok" or redis["status"] != "ok":
        overall = "degraded"

    return {
        "status": overall,
        "database": database,
        "redis": redis,
    }
