from uuid import UUID
from uuid import uuid4

import asyncpg
import pytest

from src.domain.user.entities.user import UserId
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.errors import UserAlreadyExistsError
from src.domain.user.errors import UserNotFoundError
from src.domain.user.value_objects.password_hash import PasswordHash
from src.infrastructure.database.postgres.repositories.user_repository import (
    PostgresUserRepository,
)


class TestPostgresUserRepositoryCreate:
    """Tests for creating users."""

    async def test_create_user_success(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test creating a user successfully."""
        email = f"test_{uuid4().hex[:8]}@example.com"
        password_hash = PasswordHash(value="$2b$04$test_hash_value")

        user = await user_repository.create(email, password_hash)  # type: ignore[arg-type]  # EmailStr accepts str

        assert user.email == email
        assert user.password_hash.value == password_hash.value
        assert user.status == UserStatus.PENDING
        assert isinstance(user.public_id, UserPublicId)
        assert user.public_id.prefix == UserPublicId.PREFIX

    async def test_create_user_duplicate_email_raises_error(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test that creating a user with duplicate email raises UserAlreadyExistsError."""
        email = "duplicate@example.com"  # type: ignore[assignment]
        password_hash = PasswordHash(value="$2b$04$test_hash_value")

        # Create first user
        await user_repository.create(email, password_hash)  # type: ignore[arg-type]

        # Try to create duplicate - should raise error
        with pytest.raises(UserAlreadyExistsError) as exc_info:
            await user_repository.create(email, password_hash)  # type: ignore[arg-type]

        assert str(email) in str(exc_info.value)  # type: ignore[arg-type]


class TestPostgresUserRepositoryFindById:
    """Tests for finding users by ID."""

    async def test_find_by_id_success(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test finding a user by ID."""
        email = f"findbyid_{uuid4().hex[:8]}@example.com"
        password_hash = PasswordHash(value="$2b$04$test_hash_value")

        created_user = await user_repository.create(email, password_hash)  # type: ignore[arg-type]
        found_user = await user_repository.find_by_id(created_user.id)

        assert found_user.id == created_user.id
        assert found_user.email == email
        assert found_user.password_hash.value == password_hash.value
        assert found_user.status == UserStatus.PENDING

    async def test_find_by_id_not_found_raises_error(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test that finding a non-existent user raises UserNotFoundError."""
        non_existent_id = UserId(99999)

        with pytest.raises(UserNotFoundError) as exc_info:
            await user_repository.find_by_id(non_existent_id)

        assert str(non_existent_id) in str(exc_info.value)


class TestPostgresUserRepositoryFindByPublicId:
    """Tests for finding users by public ID."""

    async def test_find_by_public_id_success(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test finding a user by public ID."""
        email = f"findbypublicid_{uuid4().hex[:8]}@example.com"
        password_hash = PasswordHash(value="$2b$04$test_hash_value")

        created_user = await user_repository.create(email, password_hash)  # type: ignore[arg-type]
        found_user = await user_repository.find_by_public_id(created_user.public_id)

        assert found_user.id == created_user.id
        assert found_user.public_id == created_user.public_id
        assert found_user.email == email

    async def test_find_by_public_id_not_found_raises_error(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test that finding a non-existent user by public ID raises UserNotFoundError."""
        non_existent_public_id = UserPublicId.generate()

        with pytest.raises(UserNotFoundError) as exc_info:
            await user_repository.find_by_public_id(non_existent_public_id)

        assert str(non_existent_public_id) in str(exc_info.value)


class TestPostgresUserRepositoryFindByEmail:
    """Tests for finding users by email."""

    async def test_find_by_email_success(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test finding a user by email."""
        email = f"findbyemail_{uuid4().hex[:8]}@example.com"
        password_hash = PasswordHash(value="$2b$04$test_hash_value")

        created_user = await user_repository.create(email, password_hash)  # type: ignore[arg-type]
        found_user = await user_repository.find_by_email(str(email))  # type: ignore[arg-type]

        assert found_user.id == created_user.id
        assert found_user.email == email

    async def test_find_by_email_not_found_raises_error(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test that finding a non-existent user by email raises UserNotFoundError."""
        non_existent_email = "nonexistent@example.com"

        with pytest.raises(UserNotFoundError) as exc_info:
            await user_repository.find_by_email(non_existent_email)

        assert non_existent_email in str(exc_info.value)


class TestPostgresUserRepositorySetStatus:
    """Tests for updating user status."""

    async def test_set_status_success(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test updating user status."""
        email = f"setstatus_{uuid4().hex[:8]}@example.com"
        password_hash = PasswordHash(value="$2b$04$test_hash_value")

        created_user = await user_repository.create(email, password_hash)  # type: ignore[arg-type]
        assert created_user.status == UserStatus.PENDING

        updated_user = await user_repository.set_status(
            created_user.id, UserStatus.ACTIVE
        )

        assert updated_user.id == created_user.id
        assert updated_user.status == UserStatus.ACTIVE
        assert updated_user.email == email

    async def test_set_status_not_found_raises_error(
        self,
        user_repository: PostgresUserRepository,
    ) -> None:
        """Test that updating status of non-existent user raises UserNotFoundError."""
        non_existent_id = UserId(99999)

        with pytest.raises(UserNotFoundError) as exc_info:
            await user_repository.set_status(non_existent_id, UserStatus.ACTIVE)

        assert str(non_existent_id) in str(exc_info.value)


class TestPostgresUserRepositoryDataMapper:
    """Tests for data mapping between database rows and entities."""

    async def test_public_id_storage_and_retrieval(
        self,
        user_repository: PostgresUserRepository,
        db_connection: asyncpg.pool.PoolConnectionProxy,
    ) -> None:
        """Test that public_id is correctly stored and retrieved from database."""

        email = f"publicidtest_{uuid4().hex[:8]}@example.com"
        password_hash = PasswordHash(value="$2b$04$test_hash_value")

        user = await user_repository.create(email, password_hash)  # type: ignore[arg-type]  # EmailStr accepts str

        # Verify the UUID is stored correctly in the database
        row = await db_connection.fetchrow(
            "SELECT public_id FROM users WHERE id = $1", user.id
        )
        assert row is not None

        # The database stores just the UUID (without prefix)
        stored_uuid = row["public_id"]
        assert isinstance(stored_uuid, UUID)
        assert stored_uuid == user.public_id.uuid_v7

        # Verify we can reconstruct the full public_id
        retrieved_user = await user_repository.find_by_public_id(user.public_id)
        assert retrieved_user.public_id == user.public_id
        assert retrieved_user.public_id.prefix == UserPublicId.PREFIX
