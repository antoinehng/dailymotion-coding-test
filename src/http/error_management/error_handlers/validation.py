from fastapi import Request
from fastapi import status
from fastapi.exceptions import RequestValidationError

from src.http.error_management.error_code import HttpErrorCode
from src.http.error_management.error_response import ErrorResponseException
from src.http.error_management.error_utils import format_error_response


async def validation_exception_handler(
    request: Request, exception: RequestValidationError
):
    return format_error_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code=HttpErrorCode.HTTP_422,
        message="Validation Error",
        exceptions=[
            ErrorResponseException(
                type="".join(map(str.capitalize, error["type"].split("_"))),
                message=(
                    f"{error['loc']}: {error['msg']}"
                    + (f" value={error['input']}" if error["input"] else "")
                ),
            )
            for error in exception.errors()
        ],
    )
