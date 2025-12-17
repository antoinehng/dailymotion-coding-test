from datetime import UTC
from datetime import datetime
from datetime import timedelta
from uuid import uuid4

import asyncpg
import pytest

from src.domain.user.entities.activation_code import ActivationCode
from src.domain.user.entities.activation_code import ActivationCodeStatus
from src.domain.user.entities.user import UserId
from src.domain.user.errors import ActivationCodeNotFoundError
from src.domain.user.value_objects.password_hash import PasswordHash
from src.infrastructure.database.postgres.repositories.activation_code_repository import (
    PostgresActivationCodeRepository,
)
from src.infrastructure.database.postgres.repositories.user_repository import (
    PostgresUserRepository,
)


class TestPostgresActivationCodeRepositorySave:
    """Tests for saving activation codes."""

    async def test_save_activation_code_success(
        self,
        activation_code_repository: PostgresActivationCodeRepository,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test saving an activation code."""
        # Create a user first (required for foreign key)
        unique_email = f"test_{uuid4().hex[:8]}@example.com"
        user = await user_repository.create(
            unique_email, PasswordHash(value="$2b$04$test_hash")
        )
        user_id = user.id
        code = "1234"
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        activation_code = ActivationCode(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )

        await activation_code_repository.save(activation_code)

        # Verify it was saved by retrieving it
        retrieved = await activation_code_repository.find_by_user_id_and_code(
            user_id, code
        )

        assert retrieved.user_id == user_id
        assert retrieved.code == code
        assert retrieved.status == ActivationCodeStatus.PENDING
        # Compare timestamps (allowing small difference for database precision)
        assert abs((retrieved.expires_at - expires_at).total_seconds()) < 1

    async def test_save_updates_existing_activation_code(
        self,
        activation_code_repository: PostgresActivationCodeRepository,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test that saving an activation code updates it if it already exists."""
        # Create a user first (required for foreign key)
        unique_email = f"test2_{uuid4().hex[:8]}@example.com"
        user = await user_repository.create(
            unique_email, PasswordHash(value="$2b$04$test_hash")
        )
        user_id = user.id
        code = "5678"
        initial_expires_at = datetime.now(UTC) + timedelta(hours=12)
        updated_expires_at = datetime.now(UTC) + timedelta(hours=48)

        # Save initial code
        initial_code = ActivationCode(
            user_id=user_id,
            code=code,
            expires_at=initial_expires_at,
            status=ActivationCodeStatus.PENDING,
        )
        await activation_code_repository.save(initial_code)

        # Update with new expiration
        updated_code = ActivationCode(
            user_id=user_id,
            code=code,
            expires_at=updated_expires_at,
            status=ActivationCodeStatus.PENDING,
        )
        await activation_code_repository.save(updated_code)

        # Verify it was updated
        retrieved = await activation_code_repository.find_by_user_id_and_code(
            user_id, code
        )

        assert abs((retrieved.expires_at - updated_expires_at).total_seconds()) < 1


class TestPostgresActivationCodeRepositoryFindByUserIdAndCode:
    """Tests for finding activation codes."""

    async def test_find_by_user_id_and_code_success(
        self,
        activation_code_repository: PostgresActivationCodeRepository,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test finding an activation code by user ID and code."""
        # Create a user first (required for foreign key)
        unique_email = f"test3_{uuid4().hex[:8]}@example.com"
        user = await user_repository.create(
            unique_email, PasswordHash(value="$2b$04$test_hash")
        )
        user_id = user.id
        code = "ABCD"
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        activation_code = ActivationCode(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )

        await activation_code_repository.save(activation_code)

        found_code = await activation_code_repository.find_by_user_id_and_code(
            user_id, code
        )

        assert found_code.user_id == user_id
        assert found_code.code == code
        assert found_code.status == ActivationCodeStatus.PENDING

    async def test_find_by_user_id_and_code_not_found_raises_error(
        self,
        activation_code_repository: PostgresActivationCodeRepository,
    ) -> None:
        """Test that finding a non-existent activation code raises ActivationCodeNotFoundError."""
        non_existent_user_id = UserId(99999)
        non_existent_code = "XXXX"

        with pytest.raises(ActivationCodeNotFoundError) as exc_info:
            await activation_code_repository.find_by_user_id_and_code(
                non_existent_user_id, non_existent_code
            )

        assert str(non_existent_user_id) in str(exc_info.value)
        assert non_existent_code in str(exc_info.value)


class TestPostgresActivationCodeRepositoryMarkAsUsed:
    """Tests for marking activation codes as used."""

    async def test_mark_as_used_success(
        self,
        activation_code_repository: PostgresActivationCodeRepository,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test marking an activation code as used."""
        # Create a user first (required for foreign key)
        unique_email = f"test_mark_used_{uuid4().hex[:8]}@example.com"
        user = await user_repository.create(
            unique_email, PasswordHash(value="$2b$04$test_hash")
        )
        user_id = user.id
        code = "9999"
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        activation_code = ActivationCode(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )

        await activation_code_repository.save(activation_code)

        # Mark as used
        await activation_code_repository.mark_as_used(user_id)

        # Verify status was updated
        retrieved = await activation_code_repository.find_by_user_id_and_code(
            user_id, code
        )

        assert retrieved.status == ActivationCodeStatus.USED

    async def test_mark_as_used_only_affects_pending_codes(
        self,
        activation_code_repository: PostgresActivationCodeRepository,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test that mark_as_used only affects codes with PENDING status."""
        # Create a user first (required for foreign key)
        unique_email = f"test5_{uuid4().hex[:8]}@example.com"
        user = await user_repository.create(
            unique_email, PasswordHash(value="$2b$04$test_hash")
        )
        user_id = user.id
        pending_code = "1111"
        used_code = "2222"
        expires_at = datetime.now(UTC) + timedelta(hours=24)

        # Create a pending code
        pending_activation_code = ActivationCode(
            user_id=user_id,
            code=pending_code,
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )
        await activation_code_repository.save(pending_activation_code)

        # Create an already-used code
        used_activation_code = ActivationCode(
            user_id=user_id,
            code=used_code,
            expires_at=expires_at,
            status=ActivationCodeStatus.USED,
        )
        await activation_code_repository.save(used_activation_code)

        # Mark as used (should only affect pending code)
        await activation_code_repository.mark_as_used(user_id)

        # Verify pending code was updated
        pending_retrieved = await activation_code_repository.find_by_user_id_and_code(
            user_id, pending_code
        )
        assert pending_retrieved.status == ActivationCodeStatus.USED

        # Verify used code remains used
        used_retrieved = await activation_code_repository.find_by_user_id_and_code(
            user_id, used_code
        )
        assert used_retrieved.status == ActivationCodeStatus.USED


class TestPostgresActivationCodeRepositoryDataMapper:
    """Tests for data mapping between database rows and entities."""

    async def test_datetime_storage_and_retrieval(
        self,
        activation_code_repository: PostgresActivationCodeRepository,
        user_repository: PostgresUserRepository,
        db_connection: asyncpg.pool.PoolConnectionProxy,
    ) -> None:
        """Test that datetime is correctly stored and retrieved from database."""
        # Create a user first (required for foreign key)
        unique_email = f"test6_{uuid4().hex[:8]}@example.com"
        user = await user_repository.create(
            unique_email, PasswordHash(value="$2b$04$test_hash")
        )
        user_id = user.id
        code = "3333"
        expires_at = datetime.now(UTC).replace(microsecond=0) + timedelta(
            hours=1
        )  # Ensure it's in the future

        activation_code = ActivationCode(
            user_id=user_id,
            code=code,
            expires_at=expires_at,
            status=ActivationCodeStatus.PENDING,
        )

        await activation_code_repository.save(activation_code)

        # Verify the datetime is stored correctly in the database
        row = await db_connection.fetchrow(
            "SELECT expires_at FROM activation_codes WHERE user_id = $1 AND code = $2",
            user_id,
            code,
        )
        assert row is not None

        stored_datetime = row["expires_at"]
        assert isinstance(stored_datetime, datetime)
        assert stored_datetime.tzinfo is not None  # Should be timezone-aware

        # Verify we can retrieve it correctly
        retrieved = await activation_code_repository.find_by_user_id_and_code(
            user_id, code
        )
        assert retrieved.expires_at.tzinfo is not None
        assert abs((retrieved.expires_at - expires_at).total_seconds()) < 1
