from typing import Any
from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import computed_field
from pydantic import model_validator
from pydantic.alias_generators import to_camel


def redact_headers(headers: dict[str, Any]) -> dict[str, Any]:
    # Redact Authorization headers
    for header_name in headers:
        if "authorization" in header_name.lower():
            headers[header_name] = "Bearer [REDACTED]"
        elif (
            "token" in header_name.lower()
            or "key" in header_name.lower()
            or "cookie" in header_name.lower()
        ):
            headers[header_name] = "[REDACTED]"

    return headers


class ApiCallRequestContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    method: str
    url_path: str
    request_headers: dict[str, Any]

    @model_validator(mode="after")
    def redact_headers(self) -> ApiCallRequestContext:
        self.request_headers = redact_headers(self.request_headers)
        return self

    @computed_field
    def request_id(self) -> str:
        return str(
            UUID(
                hex=(self.request_headers.get("dailymotion-request-id") or str(uuid4()))
            )
        )


class ApiCallResponseContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    status_code: int
    response_time_ms: float
    response_headers: dict[str, Any]

    @model_validator(mode="after")
    def redact_headers(self) -> ApiCallResponseContext:
        self.response_headers = redact_headers(self.response_headers)
        return self

    @computed_field
    def request_id(self) -> str:
        return str(
            UUID(
                hex=(
                    self.response_headers.get("dailymotion-request-id") or str(uuid4())
                )
            )
        )
