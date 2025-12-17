from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from src.application.registration.ports.password_hasher import PasswordHasher
from src.application.registration.ports.user_repository import UserRepository
from src.application.registration.use_cases.register_user import RegisterUser
from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserId
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.errors import UserAlreadyExistsError
from src.domain.user.value_objects.password import Password
from src.domain.user.value_objects.password_hash import PasswordHash


class TestRegisterUserExecute:
    """Test RegisterUser.execute() method."""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        """Create a mock UserRepository."""
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_password_hasher(self) -> MagicMock:
        """Create a mock PasswordHasher."""
        return MagicMock(spec=PasswordHasher)

    @pytest.fixture
    def register_user(
        self,
        mock_user_repository: MagicMock,
        mock_password_hasher: MagicMock,
    ) -> RegisterUser:
        """Create RegisterUser instance with mocked dependencies."""
        return RegisterUser(
            user_repository=mock_user_repository,
            password_hasher=mock_password_hasher,
        )

    @pytest.fixture
    def sample_user(self) -> User:
        """Create a sample User entity for testing."""
        return User(
            id=UserId(1),
            public_id=UserPublicId.generate(),
            email="test@example.com",
            password_hash=PasswordHash("$2b$12$hashedpassword"),
            status=UserStatus.PENDING,
        )

    async def test_execute_creates_user_successfully(
        self,
        register_user: RegisterUser,
        mock_user_repository: MagicMock,
        mock_password_hasher: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that execute() successfully creates a user."""
        email = "test@example.com"
        password = "ValidPass123!"  # noqa: S105 - This is a test password
        password_hash = PasswordHash("$2b$12$hashedpassword")

        # Setup mocks
        mock_password_hasher.hash.return_value = password_hash
        mock_user_repository.create = AsyncMock(return_value=sample_user)

        # Execute
        result = await register_user.execute(email, password)

        # Verify password was hashed
        mock_password_hasher.hash.assert_called_once()
        assert isinstance(mock_password_hasher.hash.call_args[0][0], Password)

        # Verify user was created
        mock_user_repository.create.assert_called_once_with(email, password_hash)

        # Verify returned user
        assert result == sample_user

    async def test_execute_raises_user_already_exists_error(
        self,
        register_user: RegisterUser,
        mock_user_repository: MagicMock,
        mock_password_hasher: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that execute() raises UserAlreadyExistsError when user already exists."""
        email = "existing@example.com"
        password = "ValidPass123!"  # noqa: S105 - This is a test password
        password_hash = PasswordHash("$2b$12$hashedpassword")

        # Setup mocks
        mock_password_hasher.hash.return_value = password_hash
        mock_user_repository.create = AsyncMock(
            side_effect=UserAlreadyExistsError("User already exists.")
        )

        # Execute and verify exception
        with pytest.raises(UserAlreadyExistsError, match="User already exists"):
            await register_user.execute(email, password)

        # Verify password was hashed
        mock_password_hasher.hash.assert_called_once()

        # Verify user repository was called
        mock_user_repository.create.assert_called_once_with(email, password_hash)

    async def test_execute_validates_password_strength(
        self,
        register_user: RegisterUser,
        mock_password_hasher: MagicMock,
    ) -> None:
        """Test that execute() validates password strength before hashing."""
        email = "test@example.com"
        # Too short, missing requirements
        weak_password = "weak"  # noqa: S105 - This is a test password

        # Execute and verify exception from Password validation
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ):  # Password validation raises ExceptionGroup
            await register_user.execute(email, weak_password)

        # Verify password hasher was not called (validation failed first)
        mock_password_hasher.hash.assert_not_called()

    async def test_execute_returns_created_user(
        self,
        register_user: RegisterUser,
        mock_user_repository: MagicMock,
        mock_password_hasher: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that execute() returns the created user entity."""
        email = "test@example.com"
        password = "ValidPass123!"  # noqa: S105 - This is a test password
        password_hash = PasswordHash("$2b$12$hashedpassword")

        # Setup mocks
        mock_password_hasher.hash.return_value = password_hash
        mock_user_repository.create = AsyncMock(return_value=sample_user)

        # Execute
        result = await register_user.execute(email, password)

        # Verify returned user
        assert result == sample_user
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.status == UserStatus.PENDING
