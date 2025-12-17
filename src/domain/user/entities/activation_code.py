import random
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from src.domain.user.entities.user import UserId
from src.domain.user.errors import ActivationCodeInvalidError


class ActivationCodeStatus(StrEnum):
    """Status of an activation code."""

    PENDING = "pending"
    USED = "used"


# Constants
ACTIVATION_CODE_LENGTH = 4


class ActivationCode(BaseModel):
    """Activation code entity for user account activation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: UserId
    code: str = Field(
        ...,
        description="4-digit activation code",
        min_length=ACTIVATION_CODE_LENGTH,
        max_length=ACTIVATION_CODE_LENGTH,
    )
    expires_at: datetime
    status: ActivationCodeStatus = ActivationCodeStatus.PENDING

    @staticmethod
    def validate_code_format(code: str) -> str:
        """Validate that code is exactly 4 digits.

        Args:
            code: Code string to validate

        Returns:
            Validated code string

        Raises:
            ValueError: If code is not 4 digits
        """
        if not code.isdigit():
            raise ValueError("Activation code must contain only digits")
        if len(code) != ACTIVATION_CODE_LENGTH:
            raise ValueError(
                f"Activation code must be exactly {ACTIVATION_CODE_LENGTH} digits"
            )
        return code

    @staticmethod
    def generate_code() -> str:
        """Generate a 4-digit activation code.

        Returns:
            4-digit code as string (zero-padded)
        """
        return f"{random.randint(0, 9999):04d}"  # noqa: S311 - Random is acceptable for activation codes

    @classmethod
    def create(
        cls,
        user_id: UserId,
        expires_in_minutes: int = 1,
    ) -> ActivationCode:
        """Create a new activation code with generated code and expiration time.

        Args:
            user_id: User ID for the activation code
            expires_in_minutes: Minutes until expiration (default: 1)

        Returns:
            New ActivationCode instance
        """
        code = cls.generate_code()
        expires_at = datetime.now(UTC) + timedelta(minutes=expires_in_minutes)

        return cls(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
        )

    def is_expired(self) -> bool:
        """Check if the activation code has expired.

        Returns:
            True if code is expired, False otherwise
        """
        return datetime.now(UTC) >= self.expires_at

    def is_used(self) -> bool:
        """Check if the activation code has been used.

        Returns:
            True if code is used, False otherwise
        """
        return self.status == ActivationCodeStatus.USED

    def is_valid(self) -> bool:
        """Check if the activation code is valid (not expired and not used).

        Returns:
            True if code is valid

        Raises:
            ActivationCodeInvalidError: If code is expired or already used
        """
        if self.is_used():
            raise ActivationCodeInvalidError("Activation code has already been used.")

        if self.is_expired():
            raise ActivationCodeInvalidError(
                "Activation code has expired. Please request a new activation code."
            )

        return True
