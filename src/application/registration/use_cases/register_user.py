from src.application.registration.ports.password_hasher import PasswordHasher
from src.application.registration.ports.user_repository import UserRepository
from src.domain.user.entities.user import User
from src.domain.user.value_objects.password import Password


class RegisterUser:
    """Use case for registering a new user."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        """Initialize use case with dependencies.

        Args:
            user_repository: Repository for user persistence
            password_hasher: Service for password hashing
        """
        self._user_repository = user_repository
        self._password_hasher = password_hasher

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

        return user
