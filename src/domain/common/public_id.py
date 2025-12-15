"""Base PublicId value object for domain entities."""

from typing import ClassVar
from typing import TypeVar
from uuid import UUID
from uuid import uuid7

from pydantic import BaseModel
from pydantic import field_validator

T = TypeVar("T", bound="PublicId")


class PublicId(BaseModel):
    """Base class for public identifiers combining a prefix with UUIDv7."""

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    PREFIX: ClassVar[str]  # Subclasses must define this
    prefix: str
    uuid_v7: UUID

    def __init__(self, prefix: str, uuid_v7: UUID) -> None:
        """Initialize PublicId with prefix and UUIDv7."""
        if prefix != self.PREFIX:
            raise ValueError(
                f"Invalid prefix: expected '{self.PREFIX}', got '{prefix}'"
            )
        super().__init__(prefix=prefix, uuid_v7=uuid_v7)

    @classmethod
    def generate(cls: type[T]) -> T:
        """Generate a new PublicId with a fresh UUIDv7."""
        return cls(cls.PREFIX, uuid7())

    @classmethod
    def from_string(cls: type[T], value: str) -> T:
        """Parse PublicId from string format 'prefix_uuid'."""
        try:
            prefix, uuid_str = value.split("_", 1)
            uuid_v7 = UUID(uuid_str)
            return cls(prefix=prefix, uuid_v7=uuid_v7)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid {cls.__name__} format: {value}") from e

    @classmethod
    @field_validator("prefix", mode="before")
    def validate_prefix(cls, value: str) -> str:
        """Validate that prefix matches the expected value."""
        if value != cls.PREFIX:
            raise ValueError(f"Invalid prefix: expected '{cls.PREFIX}', got '{value}'")
        return value

    def __str__(self) -> str:
        """Return string representation: 'prefix_uuid'."""
        return f"{self.prefix}_{self.uuid_v7}"

    def __repr__(self) -> str:
        """Return representation."""
        return (
            f"{self.__class__.__name__}(prefix='{self.prefix}', uuid_v7={self.uuid_v7})"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality - only equal to same type."""
        if not isinstance(other, self.__class__):
            return False
        return self.prefix == other.prefix and self.uuid_v7 == other.uuid_v7

    def __hash__(self) -> int:
        """Return hash."""
        return hash((self.__class__, self.prefix, self.uuid_v7))
