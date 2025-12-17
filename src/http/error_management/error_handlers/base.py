from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

from src.http.error_management.error_code import HttpErrorCode
from src.http.error_management.error_utils import extract_exceptions
from src.http.error_management.error_utils import format_error_response


async def base_exception_handler(
    request: Request, exception: Exception
) -> JSONResponse:
    return format_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=HttpErrorCode.HTTP_500,
        message=str(exception),
        exceptions=[exception],
    )


async def exception_group_handler(
    request: Request, exception_group: ExceptionGroup[Exception]
) -> JSONResponse:
    return format_error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=HttpErrorCode.HTTP_500,
        message=str(exception_group),
        exceptions=extract_exceptions(exception_group),
    )
