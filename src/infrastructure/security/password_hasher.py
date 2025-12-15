import bcrypt

from src.application.registration.ports.password_hasher import PasswordHasher
from src.domain.user.password import Password
from src.domain.user.password_hash import PasswordHash


class BcryptPasswordHasher(PasswordHasher):
    """Bcrypt local adapter implementation of password hasher."""

    def hash(self, password: Password) -> PasswordHash:
        """Hash a password using bcrypt.

        Args:
            password: The password value object to hash

        Returns:
            PasswordHash value object containing the bcrypt hash
        """
        # Encode password to bytes for bcrypt
        password_bytes = password.value.encode("utf-8")
        # Generate salt and hash (bcrypt handles salt automatically)
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        # Return as string (bcrypt hash is ASCII-safe)
        return PasswordHash(value=hashed.decode("utf-8"))

    def verify(self, password: Password, password_hash: PasswordHash) -> bool:
        """Verify a password against a bcrypt hash.

        Args:
            password: The password value object to verify
            password_hash: The bcrypt hash to verify against

        Returns:
            True if password matches hash, False otherwise
        """
        password_bytes = password.value.encode("utf-8")
        hash_bytes = password_hash.value.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
