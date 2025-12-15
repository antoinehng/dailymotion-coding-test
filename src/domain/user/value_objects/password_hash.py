from dataclasses import dataclass


@dataclass(frozen=True)
class PasswordHash:
    """Hashed password value object."""

    value: str

    def __post_init__(self) -> None:
        """Validate that hash is not empty."""
        if not self.value:
            raise ValueError("Password hash cannot be empty")

    def __str__(self) -> str:
        """Return hash value."""
        return self.value

    def __repr__(self) -> str:
        """Return representation."""
        return "PasswordHash(***)"
