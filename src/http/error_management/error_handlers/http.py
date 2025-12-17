from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse

from src.http.error_management.error_code import HttpErrorCode
from src.http.error_management.error_utils import format_error_response


async def http_exception_handler(
    request: Request, exception: HTTPException
) -> JSONResponse:
    return format_error_response(
        request=request,
        status_code=exception.status_code,
        error_code=HttpErrorCode[f"HTTP_{exception.status_code}"],
        message=exception.detail,
        exceptions=[exception],
        log_as="exception" if exception.status_code >= 500 else "warning",  # noqa: PLR2004
    )
