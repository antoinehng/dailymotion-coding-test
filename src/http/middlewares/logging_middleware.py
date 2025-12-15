import time

from fastapi import Request
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from src.infrastructure.logging import getLogger
from src.infrastructure.logging.api_call_context import ApiCallRequestContext
from src.infrastructure.logging.api_call_context import ApiCallResponseContext
from src.infrastructure.logging.logger import request_context_var
from src.infrastructure.logging.logger import response_context_var

logger = getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Main dispatch method that orchestrates the request processing.
        Calls before_request and after_request methods.
        """
        # Process before request with tracing
        await self.before_request(request)

        # Execute the actual request
        response = await call_next(request)

        # Process after request with tracing
        await self.after_request(request, response)

        return response

    async def before_request(self, request: Request) -> None:
        """Set up request context and logging before the request is handled."""
        self._start_timer(request)
        self._log_request_start(request)
        self._create_request_context(request)

    async def after_request(self, request: Request, response: Response) -> None:
        """Log response and set headers after the request is processed."""
        self._add_request_id_header(response, request.state.request_context)
        self._create_response_context(request, response)
        self._log_request_end(request, response)

    def _start_timer(self, request: Request) -> None:
        """Start timing the request processing."""
        request.state.start_time = time.monotonic()

    def _create_request_context(self, request: Request) -> None:
        """Create and set the request context."""
        request_context = ApiCallRequestContext(
            method=request.method,
            url_path=request.url.path,
            request_headers=dict(request.headers),
        )
        request.state.request_context = request_context
        request_context_var.set(request_context.model_dump())

    def _log_request_start(self, request: Request) -> None:
        """Log the start of request processing."""
        logger.info(f"{request.method.upper()} {request.url.path}")

    def _add_request_id_header(
        self, response: Response, request_context: ApiCallRequestContext
    ) -> None:
        """Add the request ID to the response headers."""
        response.headers["dailymotion-request-id"] = str(request_context.request_id)

    def _create_response_context(self, request: Request, response: Response) -> None:
        """Create and set the response context with timing information."""
        elapsed_ms = (time.monotonic() - request.state.start_time) * 1_000
        response_context = ApiCallResponseContext(
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            response_headers=dict(response.headers),
        )
        response_context_var.set(response_context.model_dump())

    def _log_request_end(self, request: Request, response: Response) -> None:
        """Log the completion of request processing."""
        logger.info(
            f"{request.method.upper()} {request.url.path} {response.status_code}"
        )
