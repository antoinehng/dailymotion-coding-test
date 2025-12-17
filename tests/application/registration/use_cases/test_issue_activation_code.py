from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from src.application.registration.ports.activation_code_repository import (
    ActivationCodeRepository,
)
from src.application.registration.ports.email_service import EmailService
from src.application.registration.ports.user_repository import UserRepository
from src.application.registration.use_cases.issue_activation_code import (
    IssueActivationCode,
)
from src.domain.user.entities.activation_code import ActivationCode
from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserId
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.errors import UserNotFoundError
from src.domain.user.value_objects.password_hash import PasswordHash


class TestIssueActivationCodeExecute:
    """Test IssueActivationCode.execute() method."""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        """Create a mock UserRepository."""
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_activation_code_repository(self) -> MagicMock:
        """Create a mock ActivationCodeRepository."""
        return MagicMock(spec=ActivationCodeRepository)

    @pytest.fixture
    def mock_email_service(self) -> MagicMock:
        """Create a mock EmailService."""
        return MagicMock(spec=EmailService)

    @pytest.fixture
    def issue_activation_code(
        self,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        mock_email_service: MagicMock,
    ) -> IssueActivationCode:
        """Create IssueActivationCode instance with mocked dependencies."""
        return IssueActivationCode(
            user_repository=mock_user_repository,
            activation_code_repository=mock_activation_code_repository,
            email_service=mock_email_service,
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

    async def test_execute_issues_activation_code_successfully(
        self,
        issue_activation_code: IssueActivationCode,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        mock_email_service: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that execute() successfully issues an activation code."""
        user_id = sample_user.id

        # Setup mocks
        mock_user_repository.find_by_id = AsyncMock(return_value=sample_user)
        mock_activation_code_repository.save = AsyncMock()
        mock_email_service.send_activation_code = AsyncMock()

        # Execute
        result = await issue_activation_code.execute(user_id)

        # Verify user was found
        mock_user_repository.find_by_id.assert_called_once_with(user_id)

        # Verify activation code was created and saved
        mock_activation_code_repository.save.assert_called_once()
        saved_activation_code = mock_activation_code_repository.save.call_args[0][0]
        assert isinstance(saved_activation_code, ActivationCode)
        assert saved_activation_code.user_id == sample_user.id
        assert len(saved_activation_code.code) == 4  # noqa: PLR2004
        assert saved_activation_code.code.isdigit()

        # Verify email was sent with activation code
        mock_email_service.send_activation_code.assert_called_once_with(
            sample_user.email, saved_activation_code.code
        )

        # Verify returned user
        assert result == sample_user

    async def test_execute_raises_user_not_found_error(
        self,
        issue_activation_code: IssueActivationCode,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        mock_email_service: MagicMock,
    ) -> None:
        """Test that execute() raises UserNotFoundError when user not found."""
        user_id = UserId(999)

        # Setup mocks
        mock_user_repository.find_by_id = AsyncMock(
            side_effect=UserNotFoundError("User not found.")
        )

        # Execute and verify exception
        with pytest.raises(UserNotFoundError, match="User not found"):
            await issue_activation_code.execute(user_id)

        # Verify user lookup was attempted
        mock_user_repository.find_by_id.assert_called_once_with(user_id)

        # Verify activation code was not created
        mock_activation_code_repository.save.assert_not_called()

        # Verify email was not sent
        mock_email_service.send_activation_code.assert_not_called()

    async def test_execute_creates_activation_code_with_correct_user_id(
        self,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        mock_email_service: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that activation code is created with the correct user ID."""
        user_id = sample_user.id

        # Setup mocks
        mock_user_repository.find_by_id = AsyncMock(return_value=sample_user)
        mock_activation_code_repository.save = AsyncMock()
        mock_email_service.send_activation_code = AsyncMock()

        # Create IssueActivationCode instance
        issue_activation_code = IssueActivationCode(
            user_repository=mock_user_repository,
            activation_code_repository=mock_activation_code_repository,
            email_service=mock_email_service,
        )

        # Execute
        await issue_activation_code.execute(user_id)

        # Verify activation code was created with correct user ID
        saved_activation_code = mock_activation_code_repository.save.call_args[0][0]
        assert saved_activation_code.user_id == sample_user.id

    async def test_execute_sends_email_with_activation_code(
        self,
        issue_activation_code: IssueActivationCode,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        mock_email_service: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that email is sent with the generated activation code."""
        user_id = sample_user.id

        # Setup mocks
        mock_user_repository.find_by_id = AsyncMock(return_value=sample_user)
        mock_activation_code_repository.save = AsyncMock()
        mock_email_service.send_activation_code = AsyncMock()

        # Execute
        await issue_activation_code.execute(user_id)

        # Verify email was sent with the activation code
        mock_email_service.send_activation_code.assert_called_once()
        call_args = mock_email_service.send_activation_code.call_args
        assert call_args[0][0] == sample_user.email
        assert len(call_args[0][1]) == 4  # noqa: PLR2004 - Activation code is 4 digits
        assert call_args[0][1].isdigit()

    async def test_execute_returns_user(
        self,
        issue_activation_code: IssueActivationCode,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        mock_email_service: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that execute() returns the user entity."""
        user_id = sample_user.id

        # Setup mocks
        mock_user_repository.find_by_id = AsyncMock(return_value=sample_user)
        mock_activation_code_repository.save = AsyncMock()
        mock_email_service.send_activation_code = AsyncMock()

        # Execute
        result = await issue_activation_code.execute(user_id)

        # Verify returned user
        assert result == sample_user
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.status == sample_user.status

    async def test_execute_creates_new_activation_code_each_time(
        self,
        issue_activation_code: IssueActivationCode,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        mock_email_service: MagicMock,
        sample_user: User,
    ) -> None:
        """Test that execute() creates a new activation code each time it's called."""
        user_id = sample_user.id

        # Setup mocks
        mock_user_repository.find_by_id = AsyncMock(return_value=sample_user)
        mock_activation_code_repository.save = AsyncMock()
        mock_email_service.send_activation_code = AsyncMock()

        # Execute twice
        await issue_activation_code.execute(user_id)
        first_code = mock_activation_code_repository.save.call_args[0][0].code

        await issue_activation_code.execute(user_id)
        second_code = mock_activation_code_repository.save.call_args[0][0].code

        # Verify two activation codes were created
        assert mock_activation_code_repository.save.call_count == 2  # noqa: PLR2004

        # Note: Codes might be the same by chance (1 in 10000), but they are
        # independent generations, so we just verify both are valid 4-digit codes
        assert len(first_code) == 4  # noqa: PLR2004
        assert len(second_code) == 4  # noqa: PLR2004
        assert first_code.isdigit()
        assert second_code.isdigit()
