from fastapi import APIRouter

from app.api.v1.endpoints import assets, auth, health, pages, projects

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(assets.router)
api_router.include_router(projects.router)
api_router.include_router(pages.router)
