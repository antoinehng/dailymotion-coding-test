from datetime import UTC
from datetime import datetime

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.application.registration.ports.activation_code_repository import (
    ActivationCodeRepository,
)
from src.domain.user.entities.activation_code import ActivationCode
from src.domain.user.entities.activation_code import ActivationCodeStatus
from src.domain.user.entities.user import UserId
from src.domain.user.errors import ActivationCodeNotFoundError


class PostgresActivationCodeDataMapper:
    """Data mapper for converting between PostgreSQL rows and ActivationCode entities."""

    @staticmethod
    def row_to_activation_code(row: asyncpg.Record) -> ActivationCode:
        """Convert database row to ActivationCode entity.

        Args:
            row: Database record

        Returns:
            ActivationCode entity
        """
        expires_at = row["expires_at"]
        if isinstance(expires_at, datetime):
            # Ensure timezone-aware datetime
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
        else:
            # Convert string to datetime if needed
            expires_at = datetime.fromisoformat(str(expires_at))

        return ActivationCode(
            user_id=UserId(row["user_id"]),
            code=row["code"],
            expires_at=expires_at,
            status=ActivationCodeStatus(row["status"]),
        )


class PostgresActivationCodeRepository(
    ActivationCodeRepository, PostgresActivationCodeDataMapper
):
    """PostgreSQL adapter for activation code persistence."""

    def __init__(self, connection: PoolConnectionProxy) -> None:
        """Initialize repository with database connection.

        Args:
            connection: AsyncPG database connection (from pool)
        """
        self._conn = connection

    async def save(self, activation_code: ActivationCode) -> None:
        """Save an activation code.

        Args:
            activation_code: The activation code entity to save
        """
        await self._conn.execute(
            """
            INSERT INTO activation_codes (user_id, code, expires_at, status)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, code) DO UPDATE
            SET expires_at = EXCLUDED.expires_at,
                status = EXCLUDED.status,
                updated_at = (NOW() AT TIME ZONE 'UTC')
            """,
            activation_code.user_id,
            activation_code.code,
            activation_code.expires_at,
            activation_code.status.value,
        )

    async def find_by_user_id_and_code(
        self, user_id: UserId, code: str
    ) -> ActivationCode:
        """Find activation code by user ID and code.

        Args:
            user_id: The user's internal ID
            code: The activation code to find

        Returns:
            ActivationCode entity if found

        Raises:
            ActivationCodeNotFoundError: If activation code not found
        """
        row = await self._conn.fetchrow(
            """
            SELECT user_id, code, expires_at, status
            FROM activation_codes
            WHERE user_id = $1 AND code = $2
            """,
            user_id,
            code,
        )

        if row is None:
            raise ActivationCodeNotFoundError(
                f"Activation code not found for user_id {user_id} and code {code}."
            )

        return self.row_to_activation_code(row)

    async def mark_as_used(self, user_id: UserId) -> None:
        """Mark activation code as used (after successful activation).

        Args:
            user_id: The user's internal ID
        """
        await self._conn.execute(
            """
            UPDATE activation_codes
            SET status = 'used', updated_at = (NOW() AT TIME ZONE 'UTC')
            WHERE user_id = $1 AND status = 'pending'
            """,
            user_id,
        )
