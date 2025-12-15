import os
from collections.abc import AsyncGenerator
from collections.abc import Generator
from unittest.mock import AsyncMock

import asyncpg
import pytest

from src.http.app import app
from src.http.dependencies.database_asyncpg import get_db_connection
from src.infrastructure.database.postgres.asyncpg_pool import close_db_pool
from src.infrastructure.database.postgres.asyncpg_pool import initialize_db_pool


@pytest.fixture(autouse=True)
def set_bcrypt_cost_factor() -> Generator[None, None, None]:  # noqa: UP043 - Explicit even if None because of yield and static type checker
    """Set lower bcrypt cost factor for faster tests.

    Bcrypt default cost factor is 12 (2^12 = 4096 rounds), which is secure but slow.
    For tests, we use cost factor 4 (2^4 = 16 rounds) which is ~250x faster while
    still testing the actual bcrypt functionality.
    """
    os.environ["BCRYPT_COST_FACTOR"] = "4"
    yield
    # Cleanup: restore default if needed
    os.environ.pop("BCRYPT_COST_FACTOR", None)


@pytest.fixture
async def db_pool() -> AsyncGenerator[None]:
    """Initialize database pool for tests.

    This fixture is available to all tests and can be used by any test that needs
    database access. If DATABASE_URL or TEST_DATABASE_URL is set, uses real database.
    Otherwise, mocks the database connection.

    This fixture helps prepare the work for integration tests. When a real database
    URL is provided, tests can run against an actual database instance, allowing
    for end-to-end testing of database operations. When no database is available,
    tests automatically fall back to mocks, making them suitable for unit testing
    without requiring database infrastructure.

    Usage:
        async def test_something(db_pool: None):
            # Database pool is initialized and available
            pass
    """
    test_db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

    if test_db_url:
        # Try to initialize real database pool
        try:
            await initialize_db_pool(
                app=app,
                database_url=test_db_url,
                min_size=1,
                max_size=2,  # Smaller pool for tests
            )
            yield
            await close_db_pool()
        except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError):
            # If database connection fails, fall back to mock
            pytest.skip("Database not available, skipping database-dependent tests")
    else:
        # Mock database connection if no DATABASE_URL is set
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=1)

        async def mock_get_db_connection():
            yield mock_conn

        app.dependency_overrides[get_db_connection] = mock_get_db_connection
        yield
        app.dependency_overrides.clear()
