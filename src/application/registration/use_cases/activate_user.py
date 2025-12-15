from src.application.registration.ports.activation_code_repository import (
    ActivationCodeRepository,
)
from src.application.registration.ports.user_repository import UserRepository
from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.errors import ActivationCodeInvalidError


class ActivateUser:
    """Use case for activating a user account with activation code."""

    def __init__(
        self,
        user_repository: UserRepository,
        activation_code_repository: ActivationCodeRepository,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            activation_code_repository: Repository for activation codes
        """
        self._user_repository = user_repository
        self._activation_code_repository = activation_code_repository

    async def execute(self, public_id: UserPublicId, code: str) -> User:
        """Activate a user account with activation code.

        Args:
            public_id: User's public ID
            activation_code: 4-digit activation code

        Returns:
            Activated user entity

        Raises:
            UserNotFoundError: If user not found
            ActivationCodeNotFoundError: If activation code not found
            ActivationCodeInvalidError: If activation code is invalid (wrong or expired)
        """
        # Find user (raises UserNotFoundError if not found)
        user = await self._user_repository.find_by_public_id(public_id)

        # Find and verify activation code
        activation_code = (
            await self._activation_code_repository.find_by_user_id_and_code(
                user.id, code
            )
        )

        if not activation_code.is_valid():
            raise ActivationCodeInvalidError()

        # Update user status to ACTIVE
        activated_user = await self._user_repository.set_status(
            user.id, UserStatus.ACTIVE
        )

        # Mark activation code as used (one-time use)
        await self._activation_code_repository.mark_as_used(user.id)

        return activated_user
