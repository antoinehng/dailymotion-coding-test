import datetime

from fastapi import APIRouter

from src.http.routes.v1.healthcheck.schemas import HealthcheckResponse
from src.http.routes.v1.healthcheck.schemas import HealthcheckStatus

router = APIRouter()


@router.get(
    "",
    response_model=HealthcheckResponse,
)
async def healthcheck() -> HealthcheckResponse:
    """Health check endpoint.

    Returns:
        Health status response
    """
    return HealthcheckResponse(
        status=HealthcheckStatus.OK,
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        message="Service is healthy",
    )
