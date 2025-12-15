"""Base PublicId value object for domain entities."""

from dataclasses import dataclass
from typing import ClassVar
from typing import TypeVar
from uuid import UUID
from uuid import uuid7

T = TypeVar("T", bound="PublicId")


@dataclass(frozen=True)
class PublicId:
    """Base class for public identifiers combining a prefix with UUIDv7."""

    PREFIX: ClassVar[str]  # Subclasses must define this
    prefix: str
    uuid_v7: UUID

    def __post_init__(self) -> None:
        """Validate that prefix matches the expected value."""
        if self.prefix != self.PREFIX:
            raise ValueError(
                f"Invalid prefix: expected '{self.PREFIX}', got '{self.prefix}'"
            )

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
        """Return hash - includes class type to ensure different types have different hashes."""
        return hash((self.__class__, self.prefix, self.uuid_v7))
