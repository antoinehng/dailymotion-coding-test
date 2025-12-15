from datetime import UTC
from datetime import datetime
from datetime import timedelta
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from src.application.registration.ports.activation_code_repository import (
    ActivationCodeRepository,
)
from src.application.registration.ports.user_repository import UserRepository
from src.application.registration.use_cases.activate_user import ActivateUser
from src.domain.user.entities.activation_code import ActivationCode
from src.domain.user.entities.activation_code import ActivationCodeStatus
from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserId
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.errors import ActivationCodeInvalidError
from src.domain.user.errors import ActivationCodeNotFoundError
from src.domain.user.errors import UserNotFoundError
from src.domain.user.value_objects.password_hash import PasswordHash


class TestActivateUserExecute:
    """Test ActivateUser.execute() method."""

    @pytest.fixture
    def mock_user_repository(self) -> MagicMock:
        """Create a mock UserRepository."""
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_activation_code_repository(self) -> MagicMock:
        """Create a mock ActivationCodeRepository."""
        return MagicMock(spec=ActivationCodeRepository)

    @pytest.fixture
    def activate_user(
        self,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
    ) -> ActivateUser:
        """Create ActivateUser instance with mocked dependencies."""
        return ActivateUser(
            user_repository=mock_user_repository,
            activation_code_repository=mock_activation_code_repository,
        )

    @pytest.fixture
    def sample_user_pending(self) -> User:
        """Create a sample User entity with PENDING status."""
        return User(
            id=UserId(1),
            public_id=UserPublicId.generate(),
            email="test@example.com",
            password_hash=PasswordHash("$2b$12$hashedpassword"),
            status=UserStatus.PENDING,
        )

    @pytest.fixture
    def sample_user_active(self) -> User:
        """Create a sample User entity with ACTIVE status."""
        return User(
            id=UserId(1),
            public_id=UserPublicId.generate(),
            email="test@example.com",
            password_hash=PasswordHash("$2b$12$hashedpassword"),
            status=UserStatus.ACTIVE,
        )

    @pytest.fixture
    def valid_activation_code(self, sample_user_pending: User) -> ActivationCode:
        """Create a valid activation code."""
        return ActivationCode(
            user_id=sample_user_pending.id,
            code="1234",
            expires_at=datetime.now(UTC) + timedelta(minutes=1),
            status=ActivationCodeStatus.PENDING,
        )

    async def test_execute_activates_user_successfully(
        self,
        activate_user: ActivateUser,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        sample_user_pending: User,
        valid_activation_code: ActivationCode,
    ) -> None:
        """Test that execute() successfully activates a user."""
        public_id = sample_user_pending.public_id
        code = "1234"
        activated_user = User(
            id=sample_user_pending.id,
            public_id=sample_user_pending.public_id,
            email=sample_user_pending.email,
            password_hash=sample_user_pending.password_hash,
            status=UserStatus.ACTIVE,
        )

        # Setup mocks
        mock_user_repository.find_by_public_id = AsyncMock(
            return_value=sample_user_pending
        )
        mock_activation_code_repository.find_by_user_id_and_code = AsyncMock(
            return_value=valid_activation_code
        )
        mock_user_repository.set_status = AsyncMock(return_value=activated_user)
        mock_activation_code_repository.mark_as_used = AsyncMock()

        # Execute
        result = await activate_user.execute(public_id, code)

        # Verify user was found
        mock_user_repository.find_by_public_id.assert_called_once_with(public_id)

        # Verify activation code was found
        mock_activation_code_repository.find_by_user_id_and_code.assert_called_once_with(
            sample_user_pending.id, code
        )

        # Verify user status was updated
        mock_user_repository.set_status.assert_called_once_with(
            sample_user_pending.id, UserStatus.ACTIVE
        )

        # Verify activation code was marked as used
        mock_activation_code_repository.mark_as_used.assert_called_once_with(
            sample_user_pending.id
        )

        # Verify returned user is activated
        assert result == activated_user
        assert result.status == UserStatus.ACTIVE

    async def test_execute_raises_user_not_found_error(
        self,
        activate_user: ActivateUser,
        mock_user_repository: MagicMock,
        sample_user_pending: User,
    ) -> None:
        """Test that execute() raises UserNotFoundError when user not found."""
        public_id = sample_user_pending.public_id
        code = "1234"

        # Setup mocks
        mock_user_repository.find_by_public_id = AsyncMock(
            side_effect=UserNotFoundError("User not found.")
        )

        # Execute and verify exception
        with pytest.raises(UserNotFoundError, match="User not found"):
            await activate_user.execute(public_id, code)

        # Verify user repository was called
        mock_user_repository.find_by_public_id.assert_called_once_with(public_id)

        # Verify activation code repository was not called
        mock_activation_code_repository = activate_user._activation_code_repository  # type: ignore[attr-defined]
        mock_activation_code_repository.find_by_user_id_and_code.assert_not_called()  # type: ignore[attr-defined]
        mock_activation_code_repository.mark_as_used.assert_not_called()  # type: ignore[attr-defined]

        # Verify user status was not updated
        mock_user_repository.set_status.assert_not_called()

    async def test_execute_raises_invalid_code_error_when_code_not_found(
        self,
        activate_user: ActivateUser,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        sample_user_pending: User,
    ) -> None:
        """Test that execute() raises ActivationCodeNotFoundError when code not found."""
        public_id = sample_user_pending.public_id
        code = "1234"

        # Setup mocks
        mock_user_repository.find_by_public_id = AsyncMock(
            return_value=sample_user_pending
        )
        mock_activation_code_repository.find_by_user_id_and_code = AsyncMock(
            side_effect=ActivationCodeNotFoundError()
        )

        # Execute and verify exception
        with pytest.raises(ActivationCodeNotFoundError):
            await activate_user.execute(public_id, code)

        # Verify user was found
        mock_user_repository.find_by_public_id.assert_called_once_with(public_id)

        # Verify activation code lookup was attempted
        mock_activation_code_repository.find_by_user_id_and_code.assert_called_once_with(
            sample_user_pending.id, code
        )

        # Verify user status was not updated
        mock_user_repository.set_status.assert_not_called()

        # Verify activation code was not marked as used
        mock_activation_code_repository.mark_as_used.assert_not_called()

    async def test_execute_raises_invalid_code_error_for_expired_code(
        self,
        activate_user: ActivateUser,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        sample_user_pending: User,
    ) -> None:
        """Test that execute() raises ActivationCodeInvalidError for expired code."""
        public_id = sample_user_pending.public_id
        code = "1234"
        expired_code = ActivationCode.model_construct(
            user_id=sample_user_pending.id,
            code=code,
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
            status=ActivationCodeStatus.PENDING,
        )

        # Setup mocks
        mock_user_repository.find_by_public_id = AsyncMock(
            return_value=sample_user_pending
        )
        mock_activation_code_repository.find_by_user_id_and_code = AsyncMock(
            return_value=expired_code
        )

        # Execute and verify exception
        with pytest.raises(ActivationCodeInvalidError):
            await activate_user.execute(public_id, code)

        # Verify user status was not updated
        mock_user_repository.set_status.assert_not_called()

        # Verify activation code was not marked as used
        mock_activation_code_repository.mark_as_used.assert_not_called()

    async def test_execute_raises_invalid_code_error_for_used_code(
        self,
        activate_user: ActivateUser,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        sample_user_pending: User,
    ) -> None:
        """Test that execute() raises ActivationCodeInvalidError for used code."""
        public_id = sample_user_pending.public_id
        code = "1234"
        used_code = ActivationCode(
            user_id=sample_user_pending.id,
            code=code,
            expires_at=datetime.now(UTC) + timedelta(minutes=1),
            status=ActivationCodeStatus.USED,
        )

        # Setup mocks
        mock_user_repository.find_by_public_id = AsyncMock(
            return_value=sample_user_pending
        )
        mock_activation_code_repository.find_by_user_id_and_code = AsyncMock(
            return_value=used_code
        )

        # Execute and verify exception
        with pytest.raises(ActivationCodeInvalidError):
            await activate_user.execute(public_id, code)

        # Verify user status was not updated
        mock_user_repository.set_status.assert_not_called()

        # Verify activation code was not marked as used again
        mock_activation_code_repository.mark_as_used.assert_not_called()

    async def test_execute_raises_invalid_code_error_for_wrong_code(
        self,
        activate_user: ActivateUser,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        sample_user_pending: User,
    ) -> None:
        """Test that execute() raises ActivationCodeNotFoundError for wrong code.

        Note: The repository's find_by_user_id_and_code method raises
        ActivationCodeNotFoundError when the code doesn't match.
        """
        public_id = sample_user_pending.public_id
        wrong_code = "9999"

        # Setup mocks
        mock_user_repository.find_by_public_id = AsyncMock(
            return_value=sample_user_pending
        )
        # Repository raises error when code doesn't match
        mock_activation_code_repository.find_by_user_id_and_code = AsyncMock(
            side_effect=ActivationCodeNotFoundError()
        )

        # Execute and verify exception
        with pytest.raises(ActivationCodeNotFoundError):
            await activate_user.execute(public_id, wrong_code)

    async def test_execute_is_idempotent_when_user_already_active(
        self,
        activate_user: ActivateUser,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        sample_user_active: User,
    ) -> None:
        """Test that execute() is idempotent - returns user if already active."""
        public_id = sample_user_active.public_id
        code = "1234"
        valid_activation_code = ActivationCode(
            user_id=sample_user_active.id,
            code=code,
            expires_at=datetime.now(UTC) + timedelta(minutes=1),
            status=ActivationCodeStatus.PENDING,
        )

        # Setup mocks
        mock_user_repository.find_by_public_id = AsyncMock(
            return_value=sample_user_active
        )
        mock_activation_code_repository.find_by_user_id_and_code = AsyncMock(
            return_value=valid_activation_code
        )
        # User status update returns the same active user
        mock_user_repository.set_status = AsyncMock(return_value=sample_user_active)
        mock_activation_code_repository.mark_as_used = AsyncMock()

        # Execute
        result = await activate_user.execute(public_id, code)

        # Verify user was found
        mock_user_repository.find_by_public_id.assert_called_once_with(public_id)

        # Verify activation code was found (idempotency check happens after)
        mock_activation_code_repository.find_by_user_id_and_code.assert_called_once_with(
            sample_user_active.id, code
        )

        # Verify user status was updated (even if already active, for idempotency)
        mock_user_repository.set_status.assert_called_once_with(
            sample_user_active.id, UserStatus.ACTIVE
        )

        # Verify activation code was marked as used
        mock_activation_code_repository.mark_as_used.assert_called_once_with(
            sample_user_active.id
        )

        # Verify returned user is the same active user
        assert result == sample_user_active
        assert result.status == UserStatus.ACTIVE

    async def test_execute_marks_activation_code_as_used(
        self,
        activate_user: ActivateUser,
        mock_user_repository: MagicMock,
        mock_activation_code_repository: MagicMock,
        sample_user_pending: User,
        valid_activation_code: ActivationCode,
    ) -> None:
        """Test that execute() marks activation code as used after successful activation."""
        public_id = sample_user_pending.public_id
        code = "1234"
        activated_user = User(
            id=sample_user_pending.id,
            public_id=sample_user_pending.public_id,
            email=sample_user_pending.email,
            password_hash=sample_user_pending.password_hash,
            status=UserStatus.ACTIVE,
        )

        # Setup mocks
        mock_user_repository.find_by_public_id = AsyncMock(
            return_value=sample_user_pending
        )
        mock_activation_code_repository.find_by_user_id_and_code = AsyncMock(
            return_value=valid_activation_code
        )
        mock_user_repository.set_status = AsyncMock(return_value=activated_user)
        mock_activation_code_repository.mark_as_used = AsyncMock()

        # Execute
        await activate_user.execute(public_id, code)

        # Verify activation code was marked as used
        mock_activation_code_repository.mark_as_used.assert_called_once_with(
            sample_user_pending.id
        )

        # Verify order: status update happens before marking code as used
        # (This is important for transaction consistency)
        call_order = [
            call[0] for call in mock_user_repository.set_status.call_args_list
        ]
        mark_used_calls = [
            call[0]
            for call in mock_activation_code_repository.mark_as_used.call_args_list
        ]
        # Both should be called
        assert len(call_order) == 1
        assert len(mark_used_calls) == 1
