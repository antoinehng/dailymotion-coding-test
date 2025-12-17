from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
from pydantic import field_validator

from src.domain.user.value_objects.password import Password


class RegisterUserRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., description="User's password", examples=["SecurePass123!"]
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password using Password value object.

        Args:
            v: Password string to validate

        Returns:
            Validated password string

        Raises:
            ValueError: If password validation fails
        """
        # Use Password value object to validate
        # This will raise ExceptionGroup if validation fails
        try:
            Password(v)
        except ExceptionGroup as e:
            # Convert ExceptionGroup to ValueError for Pydantic
            # Combine all error messages into one
            error_messages = [
                str(exc) for exc in e.exceptions if isinstance(exc, ValueError)
            ]
            error_msg = (
                "; ".join(error_messages)
                if error_messages
                else "Password validation failed"
            )
            raise ValueError(error_msg) from e
        return v


class RegisterUserResponse(BaseModel):
    """Response schema for user registration."""

    public_id: str = Field(..., description="User's public identifier")
    email: EmailStr = Field(..., description="User's email address")
    status: str = Field(..., description="User's account status")
