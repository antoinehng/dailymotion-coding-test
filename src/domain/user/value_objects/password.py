import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Password:
    """Password value object that validates password strength requirements."""

    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRES_UPPERCASE = True
    REQUIRES_LOWERCASE = True
    REQUIRES_DIGIT = True
    REQUIRES_SPECIAL_CHAR = True

    value: str

    def __post_init__(self) -> None:
        """Validate password strength requirements."""
        errors: list[str] = []

        if len(self.value) < self.MIN_LENGTH:
            errors.append(
                f"Password must be at least {self.MIN_LENGTH} characters long"
            )

        if len(self.value) > self.MAX_LENGTH:
            errors.append(f"Password must be at most {self.MAX_LENGTH} characters long")

        if self.REQUIRES_UPPERCASE and not re.search(r"[A-Z]", self.value):
            errors.append("Password must contain at least one uppercase letter")

        if self.REQUIRES_LOWERCASE and not re.search(r"[a-z]", self.value):
            errors.append("Password must contain at least one lowercase letter")

        if self.REQUIRES_DIGIT and not re.search(r"\d", self.value):
            errors.append("Password must contain at least one digit")

        if self.REQUIRES_SPECIAL_CHAR and not re.search(
            r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", self.value
        ):
            errors.append("Password must contain at least one special character")

        if errors:
            raise ExceptionGroup(
                "Password validation failed",
                [ValueError(error) for error in errors],
            )

    def __str__(self) -> str:
        """Return masked password for security."""
        return "***"

    def __repr__(self) -> str:
        """Return masked representation."""
        return "Password(***)"
