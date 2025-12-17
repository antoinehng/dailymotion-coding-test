from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from fastapi import status
from httpx import AsyncClient

from src.application.registration.use_cases.activate_user import ActivateUser
from src.application.registration.use_cases.issue_activation_code import (
    IssueActivationCode,
)
from src.application.registration.use_cases.register_user import RegisterUser
from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserId
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.errors import ActivationCodeInvalidError
from src.domain.user.errors import UserAlreadyExistsError
from src.domain.user.errors import UserNotFoundError
from src.domain.user.value_objects.password_hash import PasswordHash
from src.http.app import app
from src.http.dependencies.auth import get_authenticated_user_from_basic_auth
from src.http.dependencies.registration import get_activate_user_use_case
from src.http.dependencies.registration import get_issue_activation_code_use_case
from src.http.dependencies.registration import get_register_user_use_case


@pytest.fixture
def mock_register_user_use_case() -> MagicMock:
    """Create a mock RegisterUser use case."""
    return MagicMock(spec=RegisterUser)


@pytest.fixture
def mock_issue_activation_code_use_case() -> MagicMock:
    """Create a mock IssueActivationCode use case."""
    return MagicMock(spec=IssueActivationCode)


@pytest.fixture
def mock_activate_user_use_case() -> MagicMock:
    """Create a mock ActivateUser use case."""
    return MagicMock(spec=ActivateUser)


@pytest.fixture
def sample_user() -> User:
    """Create a sample User entity for testing."""
    return User(
        id=UserId(1),
        public_id=UserPublicId.generate(),
        email="test@example.com",
        password_hash=PasswordHash("$2b$12$hashedpassword"),
        status=UserStatus.PENDING,
    )


@pytest.fixture
def sample_active_user() -> User:
    """Create a sample active User entity for testing."""
    return User(
        id=UserId(1),
        public_id=UserPublicId.generate(),
        email="test@example.com",
        password_hash=PasswordHash("$2b$12$hashedpassword"),
        status=UserStatus.ACTIVE,
    )


class TestRegisterUserEndpoint:
    """Test POST /v1/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_user_success(
        self,
        async_client: AsyncClient,
        mock_register_user_use_case: MagicMock,
        mock_issue_activation_code_use_case: MagicMock,
        sample_user: User,
    ) -> None:
        """Test successful user registration."""
        # Setup mocks
        mock_register_user_use_case.execute = AsyncMock(return_value=sample_user)
        mock_issue_activation_code_use_case.execute = AsyncMock()

        # Override dependencies
        app.dependency_overrides[get_register_user_use_case] = (
            lambda: mock_register_user_use_case
        )
        app.dependency_overrides[get_issue_activation_code_use_case] = (
            lambda: mock_issue_activation_code_use_case
        )

        try:
            # Execute
            response = await async_client.post(
                "/v1/register",
                json={"email": "test@example.com", "password": "ValidPass123!"},
            )

            # Verify response
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["public_id"] == str(sample_user.public_id)
            assert data["email"] == sample_user.email
            assert data["status"] == sample_user.status.value

            # Verify use cases were called
            mock_register_user_use_case.execute.assert_called_once_with(
                email="test@example.com",
                password="ValidPass123!",  # noqa: S106 - Test password
            )
            mock_issue_activation_code_use_case.execute.assert_called_once_with(
                user_id=sample_user.id
            )
        finally:
            # Clean up overrides
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_user_conflict(
        self,
        async_client: AsyncClient,
        mock_register_user_use_case: MagicMock,
        mock_issue_activation_code_use_case: MagicMock,
    ) -> None:
        """Test registration with existing email returns 409."""
        # Setup mocks
        mock_register_user_use_case.execute = AsyncMock(
            side_effect=UserAlreadyExistsError("User already exists.")
        )

        # Override dependencies
        app.dependency_overrides[get_register_user_use_case] = (
            lambda: mock_register_user_use_case
        )
        app.dependency_overrides[get_issue_activation_code_use_case] = (
            lambda: mock_issue_activation_code_use_case
        )

        try:
            # Execute
            response = await async_client.post(
                "/v1/register",
                json={"email": "existing@example.com", "password": "ValidPass123!"},
            )

            # Verify response
            assert response.status_code == status.HTTP_409_CONFLICT
            data = response.json()
            assert "code" in data
            assert "message" in data
            assert data["code"] == "UserAlreadyExists"

            # Verify activation code was not issued
            mock_issue_activation_code_use_case.execute.assert_not_called()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_user_validation_error(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test registration with invalid request data returns 422."""
        # Execute with invalid data (missing password)
        response = await async_client.post(
            "/v1/register",
            json={"email": "test@example.com"},
        )

        # Verify response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestActivateUserEndpoint:
    """Test POST /v1/register/activate endpoint."""

    @pytest.mark.asyncio
    async def test_activate_user_success(
        self,
        async_client: AsyncClient,
        mock_activate_user_use_case: MagicMock,
        sample_active_user: User,
    ) -> None:
        """Test successful user activation."""
        # Setup mocks
        mock_activate_user_use_case.execute = AsyncMock(return_value=sample_active_user)

        # Mock authentication dependency
        async def mock_auth() -> User:
            return User(
                id=UserId(1),
                public_id=UserPublicId.generate(),
                email="test@example.com",
                password_hash=PasswordHash("$2b$12$hashedpassword"),
                status=UserStatus.PENDING,
            )

        # Override dependencies
        app.dependency_overrides[get_authenticated_user_from_basic_auth] = mock_auth
        app.dependency_overrides[get_activate_user_use_case] = (
            lambda: mock_activate_user_use_case
        )

        try:
            # Execute with Basic Auth
            response = await async_client.post(
                "/v1/register/activate",
                json={"code": "1234"},
                auth=("test@example.com", "ValidPass123!"),
            )

            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["public_id"] == str(sample_active_user.public_id)
            assert data["email"] == sample_active_user.email
            assert data["status"] == sample_active_user.status.value
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_activate_user_invalid_code(
        self,
        async_client: AsyncClient,
        mock_activate_user_use_case: MagicMock,
    ) -> None:
        """Test activation with invalid code returns 400."""
        # Setup mocks
        mock_activate_user_use_case.execute = AsyncMock(
            side_effect=ActivationCodeInvalidError("Activation code has expired.")
        )

        # Mock authentication dependency
        async def mock_auth() -> User:
            return User(
                id=UserId(1),
                public_id=UserPublicId.generate(),
                email="test@example.com",
                password_hash=PasswordHash("$2b$12$hashedpassword"),
                status=UserStatus.PENDING,
            )

        # Override dependencies
        app.dependency_overrides[get_authenticated_user_from_basic_auth] = mock_auth
        app.dependency_overrides[get_activate_user_use_case] = (
            lambda: mock_activate_user_use_case
        )

        try:
            # Execute
            response = await async_client.post(
                "/v1/register/activate",
                json={"code": "9999"},
                auth=("test@example.com", "ValidPass123!"),
            )

            # Verify response
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_activate_user_unauthorized(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test activation without Basic Auth returns 401."""
        # Execute without authentication
        response = await async_client.post(
            "/v1/register/activate",
            json={"code": "1234"},
        )

        # Verify response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestResendActivationCodeEndpoint:
    """Test POST /v1/register/resend-code endpoint."""

    @pytest.mark.asyncio
    async def test_resend_code_success(
        self,
        async_client: AsyncClient,
        mock_issue_activation_code_use_case: MagicMock,
        sample_user: User,
    ) -> None:
        """Test successful activation code resend."""
        # Setup mocks
        mock_issue_activation_code_use_case.execute = AsyncMock(
            return_value=sample_user
        )

        # Mock authentication dependency
        async def mock_auth() -> User:
            return sample_user

        # Override dependencies
        app.dependency_overrides[get_authenticated_user_from_basic_auth] = mock_auth
        app.dependency_overrides[get_issue_activation_code_use_case] = (
            lambda: mock_issue_activation_code_use_case
        )

        try:
            # Execute
            response = await async_client.post(
                "/v1/register/resend-code",
                auth=("test@example.com", "ValidPass123!"),
            )

            # Verify response
            assert response.status_code == status.HTTP_201_CREATED

            # Verify use case was called
            mock_issue_activation_code_use_case.execute.assert_called_once_with(
                user_id=sample_user.id
            )
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_resend_code_user_not_found(
        self,
        async_client: AsyncClient,
        mock_issue_activation_code_use_case: MagicMock,
    ) -> None:
        """Test resend code with user not found returns 404."""
        # Setup mocks
        mock_issue_activation_code_use_case.execute = AsyncMock(
            side_effect=UserNotFoundError("User not found.")
        )

        # Mock authentication dependency
        async def mock_auth() -> User:
            return User(
                id=UserId(999),
                public_id=UserPublicId.generate(),
                email="notfound@example.com",
                password_hash=PasswordHash("$2b$12$hashedpassword"),
                status=UserStatus.PENDING,
            )

        # Override dependencies
        app.dependency_overrides[get_authenticated_user_from_basic_auth] = mock_auth
        app.dependency_overrides[get_issue_activation_code_use_case] = (
            lambda: mock_issue_activation_code_use_case
        )

        try:
            # Execute
            response = await async_client.post(
                "/v1/register/resend-code",
                auth=("notfound@example.com", "ValidPass123!"),
            )

            # Verify response
            assert response.status_code == status.HTTP_404_NOT_FOUND
        finally:
            app.dependency_overrides.clear()


class TestGetCurrentUserEndpoint:
    """Test GET /v1/register/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        async_client: AsyncClient,
        sample_user: User,
    ) -> None:
        """Test successful retrieval of current user."""

        # Mock authentication dependency
        async def mock_auth() -> User:
            return sample_user

        # Override dependencies
        app.dependency_overrides[get_authenticated_user_from_basic_auth] = mock_auth

        try:
            # Execute
            response = await async_client.get(
                "/v1/register/me",
                auth=("test@example.com", "ValidPass123!"),
            )

            # Verify response
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["public_id"] == str(sample_user.public_id)
            assert data["email"] == sample_user.email
            assert data["status"] == sample_user.status.value
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test get current user without Basic Auth returns 401."""
        # Execute without authentication
        response = await async_client.get("/v1/register/me")

        # Verify response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
