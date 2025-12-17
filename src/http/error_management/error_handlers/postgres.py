from asyncpg import PostgresError
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

from src.http.error_management.error_code import DatabaseErrorCode
from src.http.error_management.error_utils import format_error_response


async def postgres_exception_handler(
    request: Request, exception: PostgresError
) -> JSONResponse:
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = DatabaseErrorCode.DB_ERROR

    return format_error_response(
        request=request,
        status_code=status_code,
        error_code=error_code,
        message=str(exception),
        exceptions=[exception],
    )
