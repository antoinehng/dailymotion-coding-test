from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest
from pydantic import ValidationError

from src.domain.user.entities.activation_code import ActivationCode
from src.domain.user.entities.activation_code import ActivationCodeStatus
from src.domain.user.entities.user import UserId
from src.domain.user.errors import ActivationCodeInvalidError


class TestActivationCodeFieldValidation:
    """Test ActivationCode field validation."""

    def test_code_must_be_exactly_4_characters(self) -> None:
        """Test that code must be exactly 4 characters."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        # Valid 4-character code
        code = ActivationCode(user_id=user_id, code="0123", expires_at=expires_at)
        assert code.code == "0123"

        # Too short (3 characters)
        with pytest.raises(ValidationError) as exc_info:
            ActivationCode(user_id=user_id, code="123", expires_at=expires_at)
        error_str = str(exc_info.value).lower()
        assert "at least 4 characters" in error_str or "string_too_short" in error_str

        # Too long (5 characters)
        with pytest.raises(ValidationError) as exc_info:
            ActivationCode(user_id=user_id, code="12345", expires_at=expires_at)
        error_str = str(exc_info.value).lower()
        assert "at most 4 characters" in error_str or "string_too_long" in error_str

    def test_expires_at_can_be_in_past(self) -> None:
        """Test that expires_at can be in the past (for loading expired codes from DB).

        Note: Expired codes can be created to allow loading from database.
        Validation happens when checking is_valid() instead.
        """
        user_id = UserId(1)

        # Valid future time
        future_time = datetime.now(UTC) + timedelta(minutes=1)
        code = ActivationCode(user_id=user_id, code="1234", expires_at=future_time)
        assert code.expires_at == future_time

        # Past time can be created (needed for loading expired codes from database)
        past_time = datetime.now(UTC) - timedelta(minutes=1)
        expired_code = ActivationCode.model_construct(
            user_id=user_id,
            code="1234",
            expires_at=past_time,
            status=ActivationCodeStatus.PENDING,
        )
        assert expired_code.expires_at == past_time
        # Validation happens when checking validity
        with pytest.raises(ActivationCodeInvalidError, match="expired"):
            expired_code.is_valid()

    def test_default_status_is_pending(self) -> None:
        """Test that default status is PENDING."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        code = ActivationCode(user_id=user_id, code="1234", expires_at=expires_at)
        assert code.status == ActivationCodeStatus.PENDING

    def test_status_can_be_set_to_used(self) -> None:
        """Test that status can be set to USED."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        code = ActivationCode(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.USED,
        )
        assert code.status == ActivationCodeStatus.USED

    def test_model_is_frozen(self) -> None:
        """Test that ActivationCode is immutable (frozen)."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        code = ActivationCode(user_id=user_id, code="1234", expires_at=expires_at)

        # Attempting to modify should raise an error (Pydantic raises ValidationError for frozen models)
        with pytest.raises((ValidationError, AttributeError)):
            code.code = "5678"  # type: ignore[misc]


class TestActivationCodeGenerateCode:
    """Test ActivationCode.generate_code() static method."""

    def test_generate_code_returns_4_digit_string(self) -> None:
        """Test that generate_code returns a 4-digit string."""
        code = ActivationCode.generate_code()
        assert len(code) == 4  # noqa: PLR2004
        assert code.isdigit()

    def test_generate_code_is_zero_padded(self) -> None:
        """Test that generate_code zero-pads single digit codes."""
        # Run multiple times to increase chance of getting a small number
        codes = [ActivationCode.generate_code() for _ in range(100)]
        assert all(len(code) == 4 for code in codes)  # noqa: PLR2004
        assert all(code.isdigit() for code in codes)

    def test_generate_code_range(self) -> None:
        """Test that generate_code generates codes in valid range."""
        codes = [ActivationCode.generate_code() for _ in range(100)]
        for code in codes:
            assert 0 <= int(code) <= 9999  # noqa: PLR2004


class TestActivationCodeCreate:
    """Test ActivationCode.create() class method."""

    def test_create_generates_code(self) -> None:
        """Test that create() generates a valid code."""
        user_id = UserId(1)
        code = ActivationCode.create(user_id=user_id)

        assert len(code.code) == 4  # noqa: PLR2004
        assert code.code.isdigit()
        assert code.user_id == user_id

    def test_create_sets_expiration_time(self) -> None:
        """Test that create() sets expiration time correctly."""
        user_id = UserId(1)
        expires_in_minutes = 5

        before = datetime.now(UTC)
        code = ActivationCode.create(
            user_id=user_id, expires_in_minutes=expires_in_minutes
        )
        after = datetime.now(UTC)

        expected_min = before + timedelta(minutes=expires_in_minutes)
        expected_max = after + timedelta(minutes=expires_in_minutes)

        assert expected_min <= code.expires_at <= expected_max

    def test_create_default_expires_in_one_minute(self) -> None:
        """Test that create() defaults to 1 minute expiration."""
        user_id = UserId(1)

        before = datetime.now(UTC)
        code = ActivationCode.create(user_id=user_id)
        after = datetime.now(UTC)

        expected_min = before + timedelta(minutes=1)
        expected_max = after + timedelta(minutes=1)

        assert expected_min <= code.expires_at <= expected_max

    def test_create_sets_status_to_pending(self) -> None:
        """Test that create() sets status to PENDING."""
        user_id = UserId(1)
        code = ActivationCode.create(user_id=user_id)

        assert code.status == ActivationCodeStatus.PENDING


class TestActivationCodeIsExpired:
    """Test ActivationCode.is_expired() method."""

    def test_is_expired_returns_false_for_future_time(self) -> None:
        """Test that is_expired() returns False for future expiration."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        code = ActivationCode(user_id=user_id, code="1234", expires_at=expires_at)
        assert code.is_expired() is False

    def test_is_expired_returns_true_for_past_time(self) -> None:
        """Test that is_expired() returns True for past expiration."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) - timedelta(minutes=1)

        # Create a code with past time using model_construct to bypass validation
        expired_code = ActivationCode.model_construct(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )
        assert expired_code.is_expired() is True

    def test_is_expired_returns_true_for_current_time(self) -> None:
        """Test that is_expired() returns True when expires_at equals current time."""
        user_id = UserId(1)
        # Use a time very close to now, but slightly in the past
        expires_at = datetime.now(UTC) - timedelta(seconds=1)

        expired_code = ActivationCode.model_construct(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )
        assert expired_code.is_expired() is True


class TestActivationCodeIsUsed:
    """Test ActivationCode.is_used() method."""

    def test_is_used_returns_false_for_pending_status(self) -> None:
        """Test that is_used() returns False for PENDING status."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        code = ActivationCode(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )
        assert code.is_used() is False

    def test_is_used_returns_true_for_used_status(self) -> None:
        """Test that is_used() returns True for USED status."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        code = ActivationCode(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.USED,
        )
        assert code.is_used() is True


class TestActivationCodeIsValid:
    """Test ActivationCode.is_valid() method."""

    def test_is_valid_returns_true_for_valid_code(self) -> None:
        """Test that is_valid() returns True for valid (pending, not expired) code."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        code = ActivationCode(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )
        assert code.is_valid() is True

    def test_is_valid_raises_error_for_used_code(self) -> None:
        """Test that is_valid() raises ActivationCodeInvalidError for used code."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) + timedelta(minutes=1)

        code = ActivationCode(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.USED,
        )
        with pytest.raises(ActivationCodeInvalidError, match="already been used"):
            code.is_valid()

    def test_is_valid_raises_error_for_expired_code(self) -> None:
        """Test that is_valid() raises ActivationCodeInvalidError for expired code."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) - timedelta(minutes=1)

        expired_code = ActivationCode.model_construct(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )
        with pytest.raises(ActivationCodeInvalidError, match="expired"):
            expired_code.is_valid()

    def test_is_valid_raises_error_for_used_and_expired_code(self) -> None:
        """Test that is_valid() raises ActivationCodeInvalidError for code that is both used and expired."""
        user_id = UserId(1)
        expires_at = datetime.now(UTC) - timedelta(minutes=1)

        expired_code = ActivationCode.model_construct(
            user_id=user_id,
            code="1234",
            expires_at=expires_at,
            status=ActivationCodeStatus.USED,
        )
        # Should raise error for used code first (checked before expired)
        with pytest.raises(ActivationCodeInvalidError, match="already been used"):
            expired_code.is_valid()
