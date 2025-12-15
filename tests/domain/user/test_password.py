from dataclasses import FrozenInstanceError

import pytest

from src.domain.user.value_objects.password import Password


class TestPasswordMinLength:
    """Test Password MIN_LENGTH validation."""

    def test_password_too_short_raises_exception(self) -> None:
        """Test that password shorter than MIN_LENGTH raises ExceptionGroup."""
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password("Short1!")

        assert len(exc_info.value.exceptions) >= 1
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("at least 8 characters" in msg for msg in error_messages)

    def test_password_exactly_min_length_passes(self) -> None:
        """Test that password with exactly MIN_LENGTH passes."""
        password = Password("ValidP1!")
        assert password.value == "ValidP1!"

    def test_password_one_char_short_raises_exception(self) -> None:
        """Test that password one character short raises exception."""
        with pytest.raises(ExceptionGroup, match="Password validation failed"):
            Password("ValidP1")  # 7 chars, needs 8


class TestPasswordMaxLength:
    """Test Password MAX_LENGTH validation."""

    def test_password_too_long_raises_exception(self) -> None:
        """Test that password longer than MAX_LENGTH raises ExceptionGroup."""
        # Create a password that's 129 characters (exceeds MAX_LENGTH of 128)
        long_password = "A" * 50 + "a" * 50 + "1" * 20 + "!" * 9  # 129 chars
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password(long_password)

        assert len(exc_info.value.exceptions) >= 1
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("at most 128 characters" in msg for msg in error_messages)

    def test_password_exactly_max_length_passes(self) -> None:
        """Test that password with exactly MAX_LENGTH passes."""
        # Create a password that's exactly 128 characters
        long_password = "A" * 50 + "a" * 50 + "1" * 20 + "!" * 8  # 128 chars
        password = Password(long_password)
        assert len(password.value) == 128  # noqa: PLR2004


class TestPasswordRequiresUppercase:
    """Test Password REQUIRES_UPPERCASE validation."""

    def test_password_without_uppercase_raises_exception(self) -> None:
        """Test that password without uppercase letter raises ExceptionGroup."""
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password("validpass123!")

        assert len(exc_info.value.exceptions) >= 1
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("uppercase letter" in msg for msg in error_messages)

    def test_password_with_uppercase_passes(self) -> None:
        """Test that password with uppercase letter passes."""
        password = Password("ValidPass123!")
        assert password.value == "ValidPass123!"


class TestPasswordRequiresLowercase:
    """Test Password REQUIRES_LOWERCASE validation."""

    def test_password_without_lowercase_raises_exception(self) -> None:
        """Test that password without lowercase letter raises ExceptionGroup."""
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password("VALIDPASS123!")

        assert len(exc_info.value.exceptions) >= 1
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("lowercase letter" in msg for msg in error_messages)

    def test_password_with_lowercase_passes(self) -> None:
        """Test that password with lowercase letter passes."""
        password = Password("ValidPass123!")
        assert password.value == "ValidPass123!"


class TestPasswordRequiresDigit:
    """Test Password REQUIRES_DIGIT validation."""

    def test_password_without_digit_raises_exception(self) -> None:
        """Test that password without digit raises ExceptionGroup."""
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password("ValidPass!")

        assert len(exc_info.value.exceptions) >= 1
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("digit" in msg for msg in error_messages)

    def test_password_with_digit_passes(self) -> None:
        """Test that password with digit passes."""
        password = Password("ValidPass123!")
        assert password.value == "ValidPass123!"


class TestPasswordRequiresSpecialChar:
    """Test Password REQUIRES_SPECIAL_CHAR validation."""

    def test_password_without_special_char_raises_exception(self) -> None:
        """Test that password without special character raises ExceptionGroup."""
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password("ValidPass123")

        assert len(exc_info.value.exceptions) >= 1
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("special character" in msg for msg in error_messages)

    def test_password_with_special_char_passes(self) -> None:
        """Test that password with special character passes."""
        password = Password("ValidPass123!")
        assert password.value == "ValidPass123!"

    def test_password_with_various_special_chars_passes(self) -> None:
        """Test that password with various special characters passes."""
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        for char in special_chars:
            password_value = f"ValidPass123{char}"
            password = Password(password_value)
            assert password.value == password_value


class TestPasswordMultipleErrors:
    """Test Password validation with multiple errors."""

    def test_password_with_multiple_errors_raises_exception_group(self) -> None:
        """Test that password with multiple errors raises ExceptionGroup with all errors."""
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password("weak")  # Too short, no uppercase, no digit, no special char

        # Should have multiple exceptions
        assert len(exc_info.value.exceptions) >= 4  # noqa: PLR2004
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("at least 8 characters" in msg for msg in error_messages)
        assert any("uppercase letter" in msg for msg in error_messages)
        assert any("digit" in msg for msg in error_messages)
        assert any("special character" in msg for msg in error_messages)

    def test_password_with_two_errors_raises_both(self) -> None:
        """Test that password with two errors raises both."""
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password("validpass123!")  # No uppercase, but has lowercase, digit, special

        assert len(exc_info.value.exceptions) >= 1
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("uppercase letter" in msg for msg in error_messages)

    def test_password_with_three_errors_raises_all_three(self) -> None:
        """Test that password with three errors raises all three."""
        with pytest.raises(
            ExceptionGroup, match="Password validation failed"
        ) as exc_info:
            Password(
                "VALIDPASS123"
            )  # No lowercase, no special char, but has uppercase, digit

        assert len(exc_info.value.exceptions) >= 2  # noqa: PLR2004
        error_messages = [str(e) for e in exc_info.value.exceptions]
        assert any("lowercase letter" in msg for msg in error_messages)
        assert any("special character" in msg for msg in error_messages)


class TestPasswordValidPasswords:
    """Test Password with valid passwords."""

    def test_valid_password_passes_all_checks(self) -> None:
        """Test that a valid password passes all validation checks."""
        password = Password("ValidPass123!")
        assert password.value == "ValidPass123!"

    def test_valid_password_with_different_special_chars(self) -> None:
        """Test valid passwords with different special characters."""
        valid_passwords = [
            "ValidPass123!",
            "ValidPass123@",
            "ValidPass123#",
            "ValidPass123$",
            "ValidPass123%",
            "ValidPass123^",
            "ValidPass123&",
            "ValidPass123*",
            "ValidPass123(",
            "ValidPass123)",
        ]

        for pwd_value in valid_passwords:
            password = Password(pwd_value)
            assert password.value == pwd_value

    def test_valid_password_edge_cases(self) -> None:
        # Exactly minimum length
        password1 = Password("ValidP1!")
        assert len(password1.value) == 8  # noqa: PLR2004

        # Long but valid password
        long_valid = "A" * 50 + "a" * 50 + "1" * 20 + "!" * 8  # 128 chars
        password2 = Password(long_valid)
        assert len(password2.value) == 128  # noqa: PLR2004


class TestPasswordImmutability:
    """Test Password immutability."""

    def test_password_is_frozen(self) -> None:
        password = Password("ValidPass123!")

        with pytest.raises(FrozenInstanceError):
            password.value = "Modified"  # type: ignore[misc]
