from abc import ABC
from abc import abstractmethod

from pydantic import EmailStr

from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserId
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.value_objects.password_hash import PasswordHash


class UserRepository(ABC):
    """Port for user persistence operations."""

    @abstractmethod
    async def create(self, email: EmailStr, password_hash: PasswordHash) -> User:
        """Create a new user.

        Args:
            email: User's email address
            password_hash: User's hashed password

        Returns:
            Created user entity
        """
        ...

    @abstractmethod
    async def find_by_id(self, user_id: UserId) -> User:
        """Find a user by internal ID.

        Args:
            user_id: The user's internal ID

        Returns:
            User entity

        Raises:
            UserNotFoundError: If user not found
        """
        ...

    @abstractmethod
    async def find_by_public_id(self, public_id: UserPublicId) -> User:
        """Find a user by public ID.

        Args:
            public_id: The user's public ID

        Returns:
            User entity

        Raises:
            UserNotFoundError: If user not found
        """
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> User:
        """Find a user by email.

        Args:
            email: The user's email address

        Returns:
            User entity

        Raises:
            UserNotFoundError: If user not found
        """
        ...

    @abstractmethod
    async def set_status(self, user_id: UserId, status: UserStatus) -> User:
        """Update user status and return the updated user.

        Args:
            user_id: The user's internal ID
            status: The new status to set

        Returns:
            Updated user entity

        Raises:
            UserNotFoundError: If user not found
        """
        ...
