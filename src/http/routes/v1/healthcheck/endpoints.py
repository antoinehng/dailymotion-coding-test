import datetime

import asyncpg
from fastapi import APIRouter
from fastapi import status

from src.http.dependencies.database_asyncpg import DbConnection
from src.http.routes.v1.healthcheck.schemas import HealthcheckResponse
from src.http.routes.v1.healthcheck.schemas import HealthcheckStatus

router = APIRouter()


@router.get(
    "",
    response_model=HealthcheckResponse,
    status_code=status.HTTP_200_OK,
)
async def healthcheck(conn: DbConnection) -> HealthcheckResponse:
    """Health check endpoint with database connectivity check.

    Args:
        conn: Database connection from the pool (injected via dependency).

    Returns:
        Health status response with database connectivity status.
    """
    # Check database connectivity
    db_status = HealthcheckStatus.OK
    db_message = "Database is healthy"
    try:
        result = await conn.fetchval("SELECT 1")
        if result != 1:
            db_status = HealthcheckStatus.KO
            db_message = "Database returned unexpected result"
    except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError) as e:
        db_status = HealthcheckStatus.KO
        db_message = f"Database connection failed: {e!s}"

    # Determine overall status
    overall_status = (
        HealthcheckStatus.OK
        if db_status == HealthcheckStatus.OK
        else HealthcheckStatus.KO
    )
    message = (
        "Service is healthy"
        if overall_status == HealthcheckStatus.OK
        else f"Service unhealthy: {db_message}"
    )

    return HealthcheckResponse(
        status=overall_status,
        timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        message=message,
    )
