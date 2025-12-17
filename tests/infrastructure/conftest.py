import os
from collections.abc import AsyncGenerator
from pathlib import Path

import asyncpg
import pytest

from src.infrastructure.database.postgres.asyncpg_pool import AsyncPGPool
from src.infrastructure.database.postgres.repositories.activation_code_repository import (
    PostgresActivationCodeRepository,
)
from src.infrastructure.database.postgres.repositories.user_repository import (
    PostgresUserRepository,
)


@pytest.fixture(scope="function")
async def db_pool_for_adapters() -> AsyncGenerator[asyncpg.Pool]:
    """Create a database pool for adapter tests.

    This fixture creates a connection pool for each test. The pool is initialized
    before each test and closed after the test completes.

    Yields:
        asyncpg.Pool: Database connection pool

    Raises:
        pytest.skip: If database is not available
    """
    test_db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not test_db_url:
        pytest.skip(
            "TEST_DATABASE_URL or DATABASE_URL not set, skipping database tests"
        )

    # Create a separate pool instance for adapter tests
    pool_manager = AsyncPGPool()
    try:
        await pool_manager.initialize(
            database_url=test_db_url,
            min_size=1,
            max_size=2,  # Small pool for tests
        )
        yield pool_manager.pool
    except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError) as e:
        pytest.skip(f"Database not available: {e}")
    finally:
        await pool_manager.close()


@pytest.fixture(scope="function")
async def ensure_migrations(db_pool_for_adapters: asyncpg.Pool) -> None:
    """Ensure database migrations are applied before running adapter tests.

    This fixture runs all migration files in order to set up the database schema.
    Migrations are idempotent (safe to run multiple times) as they check for
    existing tables/indexes.

    Args:
        db_pool_for_adapters: Database connection pool
    """
    migrations_dir = (
        Path(__file__).parent.parent.parent
        / "src"
        / "infrastructure"
        / "database"
        / "postgres"
        / "migrations"
    )
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        return

    async with db_pool_for_adapters.acquire() as conn:
        for migration_file in migration_files:
            migration_sql = migration_file.read_text()
            # Migrations use CREATE IF NOT EXISTS, so they're safe to run multiple times
            try:
                await conn.execute(migration_sql)
            except asyncpg.PostgresError as e:
                # Ignore "already exists" errors for tables/indexes
                if "already exists" not in str(e).lower():
                    raise


@pytest.fixture
async def db_connection(
    db_pool_for_adapters: asyncpg.Pool,
    ensure_migrations: None,
) -> AsyncGenerator[asyncpg.pool.PoolConnectionProxy]:
    """Provide a database connection wrapped in a transaction for test isolation.

    Each test gets its own connection and transaction. The transaction is rolled back
    after the test completes, ensuring no data persists between tests.

    This fixture provides true test isolation - each test can modify the database
    without affecting other tests.

    Args:
        db_pool_for_adapters: Database connection pool
        ensure_migrations: Ensures migrations are applied

    Yields:
        PoolConnectionProxy: Database connection in a transaction
    """
    async with db_pool_for_adapters.acquire() as conn, conn.transaction():
        # Transaction is automatically rolled back when exiting the context
        yield conn  # type: ignore[misc]  # Connection is compatible with PoolConnectionProxy


@pytest.fixture
async def user_repository(
    db_connection: asyncpg.pool.PoolConnectionProxy,
) -> PostgresUserRepository:
    """Provide a PostgresUserRepository instance for testing.

    Args:
        db_connection: Database connection (from db_connection fixture)

    Returns:
        PostgresUserRepository: Repository instance
    """
    return PostgresUserRepository(connection=db_connection)


@pytest.fixture
async def activation_code_repository(
    db_connection: asyncpg.pool.PoolConnectionProxy,
) -> PostgresActivationCodeRepository:
    """Provide a PostgresActivationCodeRepository instance for testing.

    Args:
        db_connection: Database connection (from db_connection fixture)

    Returns:
        PostgresActivationCodeRepository: Repository instance
    """
    return PostgresActivationCodeRepository(connection=db_connection)
