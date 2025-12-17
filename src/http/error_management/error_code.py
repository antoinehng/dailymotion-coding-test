from enum import StrEnum

from src.domain.user.errors import UserErrorCode
from src.helpers.enum import EnumHelper


class HttpErrorCode(StrEnum):
    HTTP_400 = "BadRequest"
    HTTP_401 = "Unauthorized"
    HTTP_402 = "PaymentRequired"
    HTTP_403 = "Forbidden"
    HTTP_404 = "NotFound"
    HTTP_405 = "MethodNotAllowed"
    HTTP_406 = "NotAcceptable"
    HTTP_407 = "ProxyAuthenticationRequired"
    HTTP_408 = "RequestTimeout"
    HTTP_409 = "Conflict"
    HTTP_410 = "Gone"
    HTTP_411 = "LengthRequired"
    HTTP_412 = "PreconditionFailed"
    HTTP_413 = "RequestEntityTooLarge"
    HTTP_414 = "RequestUriTooLong"
    HTTP_415 = "UnsupportedMediaType"
    HTTP_416 = "RequestedRangeNotSatisfiable"
    HTTP_417 = "ExpectationFailed"
    HTTP_418 = "ImATeapot"
    HTTP_421 = "MisdirectedRequest"
    HTTP_422 = "UnprocessableEntity"
    HTTP_423 = "Locked"
    HTTP_424 = "FailedDependency"
    HTTP_425 = "TooEarly"
    HTTP_426 = "UpgradeRequired"
    HTTP_428 = "PreconditionRequired"
    HTTP_429 = "TooManyRequests"
    HTTP_431 = "RequestHeaderFieldsTooLarge"
    HTTP_451 = "UnavailableForLegalReasons"
    HTTP_500 = "InternalServerError"
    HTTP_501 = "NotImplemented"
    HTTP_502 = "BadGateway"
    HTTP_503 = "ServiceUnavailable"
    HTTP_504 = "GatewayTimeout"
    HTTP_505 = "HttpVersionNotSupported"
    HTTP_506 = "VariantAlsoNegotiates"
    HTTP_507 = "InsufficientStorage"
    HTTP_508 = "LoopDetected"
    HTTP_510 = "NotExtended"
    HTTP_511 = "NetworkAuthenticationRequired"


class DatabaseErrorCode(StrEnum):
    DB_ERROR = "DatabaseError"


ErrorCode = EnumHelper.merge(
    "ErrorCode",
    HttpErrorCode,
    UserErrorCode,
    DatabaseErrorCode,
)
