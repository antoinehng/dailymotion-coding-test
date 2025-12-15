from enum import StrEnum


class UserErrorCode(StrEnum):
    USER_ERROR = "UserError"
    USER_NOT_FOUND = "UserNotFound"
    USER_ALREADY_EXISTS = "UserAlreadyExists"
    ACTIVATION_CODE_NOT_FOUND = "ActivationCodeNotFound"
    ACTIVATION_CODE_INVALID = "ActivationCodeInvalid"


class UserError(Exception):
    """Base class for exceptions for user operations."""

    error_code: UserErrorCode = UserErrorCode.USER_ERROR

    def __init__(
        self,
        message: str = "An error occurred during user operation.",
    ):
        self.message = message

        super().__init__(self.message)


class UserNotFoundError(UserError):
    """Exception raised when a user is not found."""

    error_code: UserErrorCode = UserErrorCode.USER_NOT_FOUND

    def __init__(
        self,
        message: str = "User not found.",
    ):
        self.message = message

        super().__init__(self.message)


class UserAlreadyExistsError(UserError):
    """Exception raised when a user already exists."""

    error_code: UserErrorCode = UserErrorCode.USER_ALREADY_EXISTS

    def __init__(
        self,
        message: str = "User already exists.",
    ):
        self.message = message

        super().__init__(self.message)


class ActivationCodeNotFoundError(UserError):
    """Exception raised when an activation code is not found."""

    error_code: UserErrorCode = UserErrorCode.ACTIVATION_CODE_NOT_FOUND

    def __init__(
        self,
        message: str = "User activation code not found.",
    ):
        self.message = message

        super().__init__(self.message)


class ActivationCodeInvalidError(UserError):
    """Exception raised when an activation code is invalid (wrong or expired)."""

    error_code: UserErrorCode = UserErrorCode.ACTIVATION_CODE_INVALID

    def __init__(
        self,
        message: str = "Activation code is invalid. It may be wrong or expired.",
    ):
        self.message = message

        super().__init__(self.message)
