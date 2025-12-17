from uuid import UUID

import asyncpg
from asyncpg.pool import PoolConnectionProxy
from pydantic import EmailStr

from src.application.registration.ports.user_repository import UserRepository
from src.domain.user.entities.user import User
from src.domain.user.entities.user import UserId
from src.domain.user.entities.user import UserPublicId
from src.domain.user.entities.user import UserStatus
from src.domain.user.errors import UserAlreadyExistsError
from src.domain.user.errors import UserNotFoundError
from src.domain.user.value_objects.password_hash import PasswordHash


class PostgresUserDataMapper:
    """Data mapper for converting between PostgreSQL rows and User entities."""

    @staticmethod
    def row_to_user(row: asyncpg.Record) -> User:
        """Convert database row to User entity.

        Args:
            row: Database record

        Returns:
            User entity
        """
        # Reconstruct PublicId from UUID stored in database
        # The database stores just the UUID, but we need to add the prefix
        stored_uuid = row["public_id"]
        if isinstance(stored_uuid, str):
            # If it's a string, parse it as UUID
            stored_uuid = UUID(stored_uuid)
        public_id = UserPublicId(prefix=UserPublicId.PREFIX, uuid_v7=stored_uuid)

        return User(
            id=UserId(row["id"]),
            public_id=public_id,
            email=row["email"],
            password_hash=PasswordHash(value=row["password_hash"]),
            status=UserStatus(row["status"]),
        )


class PostgresUserRepository(UserRepository, PostgresUserDataMapper):
    """PostgreSQL adapter for user persistence."""

    def __init__(self, connection: PoolConnectionProxy) -> None:
        """Initialize repository with database connection.

        Args:
            connection: AsyncPG database connection (from pool)
        """
        self._conn = connection

    async def create(self, email: EmailStr, password_hash: PasswordHash) -> User:
        """Create a new user.

        Args:
            email: User's email address
            password_hash: User's hashed password

        Returns:
            Created user entity

        Raises:
            UserAlreadyExistsError: If email is already registered
        """
        # Generate public_id
        public_id = UserPublicId.generate()

        try:
            # Insert user with PENDING status
            # Store only the UUID part (uuid_v7) in the database
            row = await self._conn.fetchrow(
                """
                INSERT INTO users (public_id, email, password_hash, status)
                VALUES ($1, $2, $3, $4)
                RETURNING id, public_id, email, password_hash, status
                """,
                public_id.uuid_v7,  # Store UUID object directly
                email,
                password_hash.value,
                UserStatus.PENDING.value,
            )
        except asyncpg.UniqueViolationError as e:
            if "email" in str(e):
                raise UserAlreadyExistsError(
                    f"User with email {email} already exists."
                ) from e
            raise

        if row is None:
            raise RuntimeError("Failed to create user")

        return self.row_to_user(row)

    async def find_by_id(self, user_id: UserId) -> User:
        """Find a user by internal ID.

        Args:
            user_id: The user's internal ID

        Returns:
            User entity

        Raises:
            UserNotFoundError: If user not found
        """
        row = await self._conn.fetchrow(
            """
            SELECT id, public_id, email, password_hash, status
            FROM users
            WHERE id = $1
            """,
            user_id,
        )

        if row is None:
            raise UserNotFoundError()

        return self.row_to_user(row)

    async def find_by_public_id(self, public_id: UserPublicId) -> User:
        """Find a user by public ID.

        Args:
            public_id: The user's public ID

        Returns:
            User entity

        Raises:
            UserNotFoundError: If user not found
        """
        row = await self._conn.fetchrow(
            """
            SELECT id, public_id, email, password_hash, status
            FROM users
            WHERE public_id = $1
            """,
            public_id.uuid_v7,  # Query using UUID part
        )

        if row is None:
            raise UserNotFoundError(f"User with public_id {public_id} not found.")

        return self.row_to_user(row)

    async def find_by_email(self, email: str) -> User:
        """Find a user by email.

        Args:
            email: The user's email address

        Returns:
            User entity

        Raises:
            UserNotFoundError: If user not found
        """
        row = await self._conn.fetchrow(
            """
            SELECT id, public_id, email, password_hash, status
            FROM users
            WHERE email = $1
            """,
            email,
        )

        if row is None:
            raise UserNotFoundError(f"User with email {email} not found.")

        return self.row_to_user(row)

    async def set_status(self, user_id: UserId, status: UserStatus) -> User:
        """Update user status and return the updated user.

        Args:
            user_id: The user's internal ID
            status: The new status to set

        Returns:
            Updated user entity

        Raises:
            UserNotFoundError: If user not found
        """
        row = await self._conn.fetchrow(
            """
            UPDATE users
            SET status = $1, updated_at = (NOW() AT TIME ZONE 'UTC')
            WHERE id = $2
            RETURNING id, public_id, email, password_hash, status
            """,
            status.value,
            user_id,
        )

        if row is None:
            raise UserNotFoundError()

        return self.row_to_user(row)
