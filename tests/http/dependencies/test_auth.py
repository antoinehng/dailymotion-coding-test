from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import HTTPBasicCredentials

from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserId
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.errors import UserNotFoundError
from src.domain.user.value_objects.password import Password
from src.domain.user.value_objects.password_hash import PasswordHash
from src.http.dependencies.auth import get_authenticated_user_from_basic_auth


class TestGetAuthenticatedUserFromBasicAuth:
    """Test get_authenticated_user_from_basic_auth() dependency function."""

    @pytest.fixture
    def mock_credentials(self) -> MagicMock:
        """Create mock HTTPBasicCredentials."""
        credentials = MagicMock(spec=HTTPBasicCredentials)
        credentials.username = "test@example.com"
        credentials.password = "ValidPass123!"  # noqa: S105 - This is a test password
        return credentials

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Create mock FastAPI Request with app state."""
        request = MagicMock(spec=Request)
        request.app.state.services = MagicMock()
        return request

    @pytest.fixture
    def mock_conn(self) -> MagicMock:
        """Create mock database connection."""
        return MagicMock()

    @pytest.fixture
    def mock_password_hasher(self) -> MagicMock:
        """Create mock PasswordHasher."""
        return MagicMock()

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

    @pytest.fixture
    def mock_user_repository(self, sample_user: User) -> MagicMock:
        """Create mock UserRepository."""
        repository = MagicMock()
        repository.find_by_email = AsyncMock(return_value=sample_user)
        return repository

    @pytest.mark.asyncio
    async def test_authenticates_user_successfully(  # noqa: PLR0913
        self,
        mock_credentials: MagicMock,
        mock_request: MagicMock,
        mock_conn: MagicMock,
        mock_password_hasher: MagicMock,
        mock_user_repository: MagicMock,
        sample_user: User,
    ) -> None:
        """Test successful authentication with valid credentials."""
        # Setup mocks
        mock_request.app.state.services.password_hasher = mock_password_hasher
        mock_password_hasher.verify.return_value = True

        with patch(
            "src.http.dependencies.auth.PostgresUserRepository",
            return_value=mock_user_repository,
        ):
            # Execute
            result = await get_authenticated_user_from_basic_auth(
                credentials=mock_credentials,
                request=mock_request,
                conn=mock_conn,
            )

        # Verify user repository was called with correct email
        mock_user_repository.find_by_email.assert_called_once_with(
            mock_credentials.username
        )

        # Verify password was verified
        mock_password_hasher.verify.assert_called_once()
        verify_call_args = mock_password_hasher.verify.call_args[0]
        assert isinstance(verify_call_args[0], Password)
        assert verify_call_args[1] == sample_user.password_hash

        # Verify returned user
        assert result == sample_user

    @pytest.mark.asyncio
    async def test_raises_http_exception_when_email_missing(
        self,
        mock_request: MagicMock,
        mock_conn: MagicMock,
    ) -> None:
        """Test that missing email raises HTTPException."""
        credentials = MagicMock(spec=HTTPBasicCredentials)
        credentials.username = ""
        credentials.password = "ValidPass123!"  # noqa: S105 - This is a test password

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await get_authenticated_user_from_basic_auth(
                credentials=credentials,
                request=mock_request,
                conn=mock_conn,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing email or password" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

    @pytest.mark.asyncio
    async def test_raises_http_exception_when_password_missing(
        self,
        mock_request: MagicMock,
        mock_conn: MagicMock,
    ) -> None:
        """Test that missing password raises HTTPException."""
        credentials = MagicMock(spec=HTTPBasicCredentials)
        credentials.username = "test@example.com"
        credentials.password = ""

        # Execute and verify exception
        with pytest.raises(HTTPException) as exc_info:
            await get_authenticated_user_from_basic_auth(
                credentials=credentials,
                request=mock_request,
                conn=mock_conn,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing email or password" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

    @pytest.mark.asyncio
    async def test_raises_http_exception_when_user_not_found(
        self,
        mock_credentials: MagicMock,
        mock_request: MagicMock,
        mock_conn: MagicMock,
        mock_password_hasher: MagicMock,
    ) -> None:
        """Test that UserNotFoundError raises HTTPException."""
        # Setup mocks
        mock_request.app.state.services.password_hasher = mock_password_hasher
        mock_user_repository = MagicMock()
        mock_user_repository.find_by_email = AsyncMock(
            side_effect=UserNotFoundError("User not found.")
        )

        with (
            patch(
                "src.http.dependencies.auth.PostgresUserRepository",
                return_value=mock_user_repository,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            # Execute and verify exception
            await get_authenticated_user_from_basic_auth(
                credentials=mock_credentials,
                request=mock_request,
                conn=mock_conn,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

        # Verify password hasher was not called (user lookup failed first)
        mock_password_hasher.verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_http_exception_when_password_invalid_format(  # noqa: PLR0913
        self,
        mock_credentials: MagicMock,
        mock_request: MagicMock,
        mock_conn: MagicMock,
        mock_password_hasher: MagicMock,
        mock_user_repository: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that invalid password format (ValueError) raises HTTPException."""
        # Setup mocks
        mock_request.app.state.services.password_hasher = mock_password_hasher
        # Password validation raises ValueError for invalid format
        mock_credentials.password = "weak"  # noqa: S105 - This is a test password

        with (
            patch(
                "src.http.dependencies.auth.PostgresUserRepository",
                return_value=mock_user_repository,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            # Execute and verify exception
            await get_authenticated_user_from_basic_auth(
                credentials=mock_credentials,
                request=mock_request,
                conn=mock_conn,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

        # Verify user was found
        mock_user_repository.find_by_email.assert_called_once()

        # Verify password hasher was not called (validation failed first)
        mock_password_hasher.verify.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_http_exception_when_password_verification_fails(  # noqa: PLR0913
        self,
        mock_credentials: MagicMock,
        mock_request: MagicMock,
        mock_conn: MagicMock,
        mock_password_hasher: MagicMock,
        mock_user_repository: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that wrong password raises HTTPException."""
        # Setup mocks
        mock_request.app.state.services.password_hasher = mock_password_hasher
        mock_password_hasher.verify.return_value = False  # Password verification fails

        with (
            patch(
                "src.http.dependencies.auth.PostgresUserRepository",
                return_value=mock_user_repository,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            # Execute and verify exception
            await get_authenticated_user_from_basic_auth(
                credentials=mock_credentials,
                request=mock_request,
                conn=mock_conn,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

        # Verify user was found
        mock_user_repository.find_by_email.assert_called_once()

        # Verify password was verified
        mock_password_hasher.verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_http_exception_when_password_validation_raises_exception_group(  # noqa: PLR0913
        self,
        mock_credentials: MagicMock,
        mock_request: MagicMock,
        mock_conn: MagicMock,
        mock_password_hasher: MagicMock,
        mock_user_repository: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that ExceptionGroup from password validation raises HTTPException."""
        # Setup mocks
        mock_request.app.state.services.password_hasher = mock_password_hasher
        # Password validation raises ExceptionGroup for invalid format
        exception_group = ExceptionGroup(
            "Password validation failed", [ValueError("Too weak")]
        )

        with (
            patch(
                "src.http.dependencies.auth.PostgresUserRepository",
                return_value=mock_user_repository,
            ),
            patch(
                "src.http.dependencies.auth.Password",
                side_effect=exception_group,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            # Execute and verify exception
            await get_authenticated_user_from_basic_auth(
                credentials=mock_credentials,
                request=mock_request,
                conn=mock_conn,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in exc_info.value.detail
        assert exc_info.value.headers == {"WWW-Authenticate": "Basic"}

        # Verify user was found
        mock_user_repository.find_by_email.assert_called_once()

        # Verify password hasher was not called (validation failed first)
        mock_password_hasher.verify.assert_not_called()
