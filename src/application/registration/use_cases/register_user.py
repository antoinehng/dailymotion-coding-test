from src.application.registration.ports.activation_code_repository import (
    ActivationCodeRepository,
)
from src.application.registration.ports.email_service import EmailService
from src.application.registration.ports.password_hasher import PasswordHasher
from src.application.registration.ports.user_repository import UserRepository
from src.domain.user.entities.activation_code import ActivationCode
from src.domain.user.entities.user import User
from src.domain.user.value_objects.password import Password


class RegisterUser:
    """Use case for registering a new user."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        email_service: EmailService,
        activation_code_repository: ActivationCodeRepository,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            password_hasher: Service for password hashing
            email_service: Service for sending emails
            activation_code_repository: Repository for activation codes
        """
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._email_service = email_service
        self._activation_code_repository = activation_code_repository

    async def execute(self, email: str, password: str) -> User:
        """Register a new user.

        Args:
            email: User's email address
            password: User's plaintext password

        Returns:
            User entity

        Raises:
            UserAlreadyExistsError: If email is already registered
        """
        # Create password value object (validates password strength)
        password_vo = Password(password)

        # Hash password
        password_hash = self._password_hasher.hash(password_vo)

        # Save user (repository creates user with generated public_id and PENDING status)
        user = await self._user_repository.create(email, password_hash)

        # Create and save activation code (valid for 1 minute)
        activation_code = ActivationCode.create(user_id=user.id)
        await self._activation_code_repository.save(activation_code)

        # Send activation code via email
        await self._email_service.send_activation_code(email, activation_code.code)

        return user
