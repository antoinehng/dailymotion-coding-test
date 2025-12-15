from fastapi import APIRouter

from src.http.routes.v1.healthcheck.endpoints import router as healthcheck

router = APIRouter()


router.include_router(healthcheck, prefix="/healthcheck", tags=["status"])
