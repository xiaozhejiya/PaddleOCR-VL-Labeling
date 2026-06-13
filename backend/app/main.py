import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings

logger = logging.getLogger(__name__)

ALEMBIC_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """按配置决定是否在启动时执行 alembic upgrade head。"""
    settings = get_settings()
    if settings.auto_migrate_on_startup:
        _run_migrations()
    yield


def _run_migrations() -> None:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(ALEMBIC_DIR),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("Alembic migration succeeded")
            if result.stdout.strip():
                logger.info(result.stdout.strip())
        else:
            stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"Alembic migration failed: {stderr}")
    except FileNotFoundError:
        raise RuntimeError(
            "Alembic executable not found; cannot run startup migrations."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Alembic migration timed out after 60s.")
    except RuntimeError:
        logger.exception("Startup migration failed")
        raise
    except Exception as exc:
        logger.exception("Startup migration failed")
        raise RuntimeError("Startup migration failed.") from exc


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description="Backend API for document collection and annotation.",
        version="0.1.0",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
