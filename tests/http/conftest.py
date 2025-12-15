from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from src.http.app import app


@pytest.fixture
async def async_client(
    db_pool: None,  # Ensures pool is initialized before client
) -> AsyncGenerator[AsyncClient]:
    """Provide an async HTTP client for testing FastAPI endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
