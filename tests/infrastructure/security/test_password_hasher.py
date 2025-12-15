import pytest

from src.domain.user.value_objects.password import Password
from src.domain.user.value_objects.password_hash import PasswordHash
from src.infrastructure.security.password_hasher import BcryptPasswordHasher


class TestBcryptPasswordHasherHash:
    """Test BcryptPasswordHasher.hash() method."""

    def test_hash_returns_password_hash(self) -> None:
        """Test that hash() returns a PasswordHash instance."""
        hasher = BcryptPasswordHasher()
        password = Password("ValidPass123!")

        password_hash = hasher.hash(password)

        assert isinstance(password_hash, PasswordHash)
        assert password_hash.value is not None
        assert len(password_hash.value) > 0

    def test_hash_produces_bcrypt_format(self) -> None:
        """Test that hash produces bcrypt format (starts with $2b$)."""
        hasher = BcryptPasswordHasher()
        password = Password("ValidPass123!")

        password_hash = hasher.hash(password)

        assert password_hash.value.startswith("$2b$")
        assert len(password_hash.value) == 60  # noqa: PLR2004 - Bcrypt hash is always 60 chars

    def test_hash_produces_different_hashes_for_same_password(self) -> None:
        """Test that hashing the same password produces different hashes (due to salt)."""
        hasher = BcryptPasswordHasher()
        password = Password("ValidPass123!")

        hash1 = hasher.hash(password)
        hash2 = hasher.hash(password)

        # Hashes should be different due to random salt
        assert hash1.value != hash2.value
        # But both should verify correctly
        assert hasher.verify(password, hash1)
        assert hasher.verify(password, hash2)

    def test_hash_produces_different_hashes_for_different_passwords(self) -> None:
        """Test that different passwords produce different hashes."""
        hasher = BcryptPasswordHasher()
        password1 = Password("ValidPass123!")
        password2 = Password("AnotherPass456!")

        hash1 = hasher.hash(password1)
        hash2 = hasher.hash(password2)

        assert hash1.value != hash2.value


class TestBcryptPasswordHasherVerify:
    """Test BcryptPasswordHasher.verify() method."""

    def test_verify_returns_true_for_correct_password(self) -> None:
        """Test that verify() returns True for correct password."""
        hasher = BcryptPasswordHasher()
        password = Password("ValidPass123!")
        password_hash = hasher.hash(password)

        result = hasher.verify(password, password_hash)

        assert result is True

    def test_verify_returns_false_for_incorrect_password(self) -> None:
        """Test that verify() returns False for incorrect password."""
        hasher = BcryptPasswordHasher()
        password = Password("ValidPass123!")
        wrong_password = Password("WrongPass123!")
        password_hash = hasher.hash(password)

        result = hasher.verify(wrong_password, password_hash)

        assert result is False

    def test_verify_returns_false_for_different_hash(self) -> None:
        """Test that verify() returns False when password doesn't match hash."""
        hasher = BcryptPasswordHasher()
        password1 = Password("ValidPass123!")
        password2 = Password("AnotherPass456!")
        hash2 = hasher.hash(password2)

        result = hasher.verify(password1, hash2)

        assert result is False

    def test_verify_roundtrip(self) -> None:
        """Test that hash and verify work together correctly."""
        hasher = BcryptPasswordHasher()
        password = Password("ValidPass123!")

        # Hash the password
        password_hash = hasher.hash(password)

        # Verify it matches
        assert hasher.verify(password, password_hash)

        # Verify wrong password doesn't match
        wrong_password = Password("WrongPass123!")
        assert not hasher.verify(wrong_password, password_hash)

    def test_verify_with_multiple_passwords(self) -> None:
        """Test verifying multiple different passwords."""
        hasher = BcryptPasswordHasher()
        passwords = [
            Password("ValidPass123!"),
            Password("AnotherPass456!"),
            Password("ThirdPass789!"),
        ]

        hashes = [hasher.hash(pwd) for pwd in passwords]

        # Each password should verify against its own hash
        for password, password_hash in zip(passwords, hashes, strict=True):
            assert hasher.verify(password, password_hash)

        # But not against other hashes
        assert not hasher.verify(passwords[0], hashes[1])
        assert not hasher.verify(passwords[1], hashes[2])
        assert not hasher.verify(passwords[2], hashes[0])


class TestBcryptPasswordHasherEdgeCases:
    """Test edge cases for BcryptPasswordHasher."""

    def test_hash_with_long_password(self) -> None:
        """Test hashing a long password (within bcrypt's 72-byte limit)."""
        hasher = BcryptPasswordHasher()
        # Create a password near max length but within bcrypt's 72-byte limit
        # Using ASCII characters (1 byte each), so max 72 chars
        long_password_value = "A" * 20 + "a" * 20 + "1" * 20 + "!" * 8
        password = Password(long_password_value)

        password_hash = hasher.hash(password)

        assert isinstance(password_hash, PasswordHash)
        assert hasher.verify(password, password_hash)

    def test_hash_with_special_characters(self) -> None:
        """Test hashing password with various special characters."""
        hasher = BcryptPasswordHasher()
        special_chars_password = Password("Pass123!@#$%^&*()_+-=[]{}|;':\",./<>?`~")

        password_hash = hasher.hash(special_chars_password)

        assert isinstance(password_hash, PasswordHash)
        assert hasher.verify(special_chars_password, password_hash)

    def test_hash_with_unicode_characters(self) -> None:
        """Test hashing password with unicode characters."""
        hasher = BcryptPasswordHasher()
        unicode_password_value = "ValidPass123!àéîöü"  # noqa: S105 - This is a test password
        password = Password(unicode_password_value)
        password_hash = hasher.hash(password)

        assert isinstance(password_hash, PasswordHash)
        assert hasher.verify(password, password_hash)

    def test_verify_with_empty_hash_raises_error(self) -> None:
        """Test that verifying with empty hash raises error."""
        with pytest.raises(ValueError, match="Password hash cannot be empty"):
            PasswordHash(value="")

    def test_hash_is_deterministic_for_verification(self) -> None:
        """Test that hash can be verified multiple times correctly."""
        hasher = BcryptPasswordHasher()
        password = Password("ValidPass123!")
        password_hash = hasher.hash(password)

        for _ in range(10):
            assert hasher.verify(password, password_hash)
