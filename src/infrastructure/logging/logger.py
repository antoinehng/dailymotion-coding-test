import logging
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

from rich.logging import RichHandler

# Holds per-request context (e.g., added in logging middleware)
request_context_var: ContextVar[dict[str, Any]] = ContextVar(
    "request_context_var",
    default={},  # noqa: B039 Do not use mutable data structures for `ContextVar` defaults
)
response_context_var: ContextVar[dict[str, Any]] = ContextVar(
    "response_context_var",
    default={},  # noqa: B039 Do not use mutable data structures for `ContextVar` defaults
)


class ApiCallContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        json_fields_data: MutableMapping[str, Any] = getattr(record, "json_fields", {})
        json_fields_data.update(request_context_var.get({}))
        json_fields_data.update(response_context_var.get({}))

        record.json_fields = json_fields_data
        return True


class PrefixAdapter(logging.LoggerAdapter):  # type: ignore [reportMissingTypeArgument]
    def __init__(self, prefix: str | None = None, *args, **kwargs) -> None:  # type: ignore [reportUnknownParameterType, reportMissingParameterType]
        super().__init__(*args, **kwargs)  # type: ignore [reportUnknownMemberType, reportUnknownArgumentType]
        self.prefix: str | None = prefix

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[Any, MutableMapping[str, Any]]:
        if self.prefix:
            return f"[{self.prefix}] {msg}", kwargs
        return msg, kwargs


def getLogger(name: str | None = None, prefix: str | None = None) -> PrefixAdapter:
    logger = logging.getLogger(name)
    logger.propagate = False

    if not logger.hasHandlers():
        logger.addHandler(RichHandler())

    if not any(isinstance(f, ApiCallContextFilter) for f in logger.filters):
        logger.addFilter(ApiCallContextFilter())

    return PrefixAdapter(
        prefix=prefix,
        logger=logger,
    )
