from fastapi import APIRouter

from src.http.routes.v1.healthcheck.endpoints import router as healthcheck
from src.http.routes.v1.registration.endpoints import router as registration

router = APIRouter()


router.include_router(healthcheck, prefix="/healthcheck", tags=["status"])
router.include_router(registration, prefix="/register", tags=["registration"])
