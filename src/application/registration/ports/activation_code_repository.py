from abc import ABC
from abc import abstractmethod

from src.domain.user.entities.activation_code import ActivationCode
from src.domain.user.entities.user import UserId


class ActivationCodeRepository(ABC):
    """Port for activation code persistence operations."""

    @abstractmethod
    async def save(self, activation_code: ActivationCode) -> None:
        """Save an activation code.

        Args:
            activation_code: The activation code entity to save
        """
        ...

    @abstractmethod
    async def find_by_user_id_and_code(
        self, user_id: UserId, code: str
    ) -> ActivationCode:
        """Find activation code by user ID and code.

        Args:
            user_id: The user's internal ID
            code: The activation code to find

        Returns:
            ActivationCode entity if found

        Raises:
            ActivationCodeNotFoundError: If activation code not found
        """
        ...

    @abstractmethod
    async def mark_as_used(self, user_id: UserId) -> None:
        """Mark activation code as used (after successful activation).

        Args:
            user_id: The user's internal ID
        """
        ...
