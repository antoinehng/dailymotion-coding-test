from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

from src.domain.user.errors import ActivationCodeInvalidError
from src.domain.user.errors import ActivationCodeNotFoundError
from src.domain.user.errors import UserAlreadyExistsError
from src.domain.user.errors import UserError
from src.domain.user.errors import UserNotFoundError
from src.http.error_management.error_utils import format_error_response


async def user_exception_handler(
    request: Request, exception: UserError
) -> JSONResponse:
    """
    Handler for user-related exceptions.
    Maps user exceptions to appropriate HTTP status codes.
    """
    # Determine status code based on exception type
    match exception:
        case UserNotFoundError():
            status_code = status.HTTP_404_NOT_FOUND
        case UserAlreadyExistsError():
            status_code = status.HTTP_409_CONFLICT
        case ActivationCodeNotFoundError():
            status_code = status.HTTP_404_NOT_FOUND
        case ActivationCodeInvalidError():
            status_code = status.HTTP_400_BAD_REQUEST
        case _:
            # Default to 400 for base UserError
            status_code = status.HTTP_400_BAD_REQUEST

    return format_error_response(
        request=request,
        status_code=status_code,
        error_code=exception.error_code,
        message=exception.message,
        exceptions=[exception],
        log_as="warning",
    )
