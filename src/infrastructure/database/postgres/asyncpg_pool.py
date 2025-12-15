"""AsyncPG database connection pool implementation.

This module provides a connection pool implementation using asyncpg for PostgreSQL.
AsyncPG is a fast, pure-Python async PostgreSQL adapter.

Example usage:
    from src.infrastructure.database.postgres.asyncpg_pool import get_db_pool
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        result = await connection.fetchval("SELECT 1")
"""

import os

import asyncpg
from fastapi import FastAPI


class AsyncPGPool:
    """AsyncPG connection pool manager."""

    def __init__(self) -> None:
        """Initialize the pool manager."""
        self._pool: asyncpg.Pool | None = None

    async def initialize(
        self,
        database_url: str | None = None,
        min_size: int = 10,
        max_size: int = 20,
    ) -> None:
        """Initialize the connection pool.

        Args:
            database_url: PostgreSQL connection URL. If None, reads from DATABASE_URL env var.
            min_size: Minimum number of connections in the pool.
            max_size: Maximum number of connections in the pool.
        """
        if self._pool is not None:
            return

        if database_url is None:
            database_url = os.getenv("DATABASE_URL")
            if database_url is None:
                raise ValueError(
                    "DATABASE_URL environment variable is not set. "
                    "Either provide database_url parameter or set DATABASE_URL env var."
                )

        # Parse the URL to extract connection parameters
        # Format: postgresql://user:password@host:port/database
        self._pool = await asyncpg.create_pool(
            database_url,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,  # 60 seconds timeout for queries
        )

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        """Get the connection pool.

        Returns:
            The asyncpg connection pool.

        Raises:
            RuntimeError: If the pool has not been initialized.
        """
        if self._pool is None:
            raise RuntimeError(
                "Database pool has not been initialized. Call initialize() first."
            )
        return self._pool

    async def check_connection(self) -> bool:
        """Check if the database connection is healthy.

        Returns:
            True if the database is reachable, False otherwise.
        """
        try:
            async with self.pool.acquire() as connection:
                result = await connection.fetchval("SELECT 1")
                return result == 1
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError):
            return False


# Global pool instance
_db_pool = AsyncPGPool()


async def get_db_pool() -> asyncpg.Pool:
    """Get the database connection pool.

    Returns:
        The asyncpg connection pool.

    Raises:
        RuntimeError: If the pool has not been initialized.
    """
    return _db_pool.pool


async def initialize_db_pool(
    app: FastAPI,
    database_url: str | None = None,
    min_size: int = 10,
    max_size: int = 20,
) -> None:
    """Initialize the database pool and store it in FastAPI app state.

    Args:
        app: FastAPI application instance.
        database_url: PostgreSQL connection URL. If None, reads from DATABASE_URL env var.
        min_size: Minimum number of connections in the pool.
        max_size: Maximum number of connections in the pool.
    """
    await _db_pool.initialize(
        database_url=database_url, min_size=min_size, max_size=max_size
    )
    app.state.db_pool = _db_pool


async def close_db_pool() -> None:
    """Close the database connection pool."""
    await _db_pool.close()
