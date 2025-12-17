import datetime
from enum import StrEnum
from typing import Literal

from fastapi import Request
from fastapi.responses import JSONResponse

from src.http.error_management.error_response import ErrorResponse
from src.http.error_management.error_response import ErrorResponseDetails
from src.http.error_management.error_response import ErrorResponseException
from src.infrastructure.logging import getLogger

logger = getLogger(__name__, prefix="ErrorHandler")


def format_error_response(  # noqa: PLR0913
    status_code: int,
    error_code: StrEnum,
    message: str,
    request: Request,
    exceptions: list[Exception] | list[ErrorResponseException],
    headers: dict[str, str] | None = None,
    log_as: Literal["exception", "error", "warning", "info", "debug"] = "exception",
):
    error_response = ErrorResponse(
        status=status_code,
        code=error_code,
        message=message,
        details=ErrorResponseDetails(
            timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
            path=request.state.request_context.url_path,
            request_id=str(request.state.request_context.request_id),
            exceptions=[
                ErrorResponseException(
                    type=exception.__class__.__name__, message=str(exception)
                )
                for exception in exceptions
                if isinstance(exception, Exception)
            ]
            + [
                exception
                for exception in exceptions
                if isinstance(exception, ErrorResponseException)
            ],
        ),
    ).model_dump()

    match log_as:
        case "exception":
            logger.exception(
                f"{status_code} {error_code.name} {message}",
                extra={"error_response": error_response},
            )
        case "error":
            logger.error(
                f"{status_code} {error_code.name} {message}",
                extra={"error_response": error_response},
            )
        case "warning":
            logger.warning(
                f"{status_code} {error_code.name} {message}",
                extra={"error_response": error_response},
            )
        case "info":
            logger.info(
                f"{status_code} {error_code.name} {message}",
                extra={"error_response": error_response},
            )
        case "debug":
            logger.debug(
                f"{status_code} {error_code.name} {message}",
                extra={"error_response": error_response},
            )

    return JSONResponse(
        status_code=status_code,
        content=error_response,
        headers=headers if headers else {},
    )


def extract_exceptions(exception_group: ExceptionGroup[Exception]) -> list[Exception]:
    all_exceptions: list[Exception] = []
    for exception in exception_group.exceptions:
        if isinstance(exception, ExceptionGroup):
            all_exceptions.extend(extract_exceptions(exception))  # type: ignore
        else:
            all_exceptions.append(exception)
    return all_exceptions
