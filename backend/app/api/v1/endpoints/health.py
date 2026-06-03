from fastapi import APIRouter

from app.core.health import service_health

router = APIRouter(tags=["system"])


@router.get("/health", summary="Health Check")
async def health_check() -> dict[str, object]:
    return service_health()
