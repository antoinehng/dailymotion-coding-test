from src.application.registration.ports.activation_code_repository import (
    ActivationCodeRepository,
)
from src.application.registration.ports.email_service import EmailService
from src.application.registration.ports.user_repository import UserRepository
from src.domain.user.entities.activation_code import ActivationCode
from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserId


class IssueActivationCode:
    """Use case for issuing a new activation code for a user."""

    def __init__(
        self,
        user_repository: UserRepository,
        activation_code_repository: ActivationCodeRepository,
        email_service: EmailService,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            activation_code_repository: Repository for activation codes
            email_service: Service for sending emails
        """
        self._user_repository = user_repository
        self._activation_code_repository = activation_code_repository
        self._email_service = email_service

    async def execute(self, user_id: UserId) -> User:
        """Issue a new activation code for a user.

        Args:
            user_id: User's internal ID

        Returns:
            User entity

        Raises:
            UserNotFoundError: If user not found
        """
        # Verify user exists
        user = await self._user_repository.find_by_id(user_id)

        # Create and save new activation code (valid for 1 minute)
        activation_code = ActivationCode.create(user_id=user.id)
        await self._activation_code_repository.save(activation_code)

        # Note: We don't invalidate existing pending codes since they expire quickly (1 minute TTL).
        # Old codes will naturally expire, but for enhanced security, we could explicitly mark
        # old pending codes as a new status enum "unused" when issuing a new one to prevent any potential reuse.

        # Send activation code via email
        await self._email_service.send_activation_code(user.email, activation_code.code)

        return user
