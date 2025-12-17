from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from src.http.error_management.error_code import ErrorCode


class ErrorResponseException(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    type: str
    message: str


class ErrorResponseDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    timestamp: str
    path: str
    request_id: str
    exceptions: list[ErrorResponseException]


class ErrorResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    status: int
    code: ErrorCode  # type: ignore [reportInvalidTypeForm] Know issue since we are using `src.helpers.enum.EnumHelper.merge` to dynamically create the enum
    message: str
    details: ErrorResponseDetails
