"""Password hasher port (interface)."""

from abc import ABC
from abc import abstractmethod

from src.domain.user.password import Password
from src.domain.user.password_hash import PasswordHash


class PasswordHasher(ABC):
    """Port for password hashing operations."""

    @abstractmethod
    def hash(self, password: Password) -> PasswordHash:
        """Hash a password and return the hash.

        Args:
            password: The password value object to hash

        Returns:
            PasswordHash value object containing the hashed password
        """
        ...

    @abstractmethod
    def verify(self, password: Password, password_hash: PasswordHash) -> bool:
        """Verify a password against a hash.

        Args:
            password: The password value object to verify
            password_hash: The hash to verify against

        Returns:
            True if password matches hash, False otherwise
        """
        ...
