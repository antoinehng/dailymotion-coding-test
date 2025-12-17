from collections.abc import AsyncGenerator
from types import SimpleNamespace

import pytest
from httpx import ASGITransport
from httpx import AsyncClient

from src.http.app import app
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.infrastructure.smtp.email_service import LoggerEmailService


@pytest.fixture(autouse=True)
def ensure_app_services_initialized() -> None:
    """Ensure app.state.services is initialized for HTTP tests."""
    if not hasattr(app.state, "services") or app.state.services is None:
        # Note: These are local implementations (BcryptPasswordHasher, LoggerEmailService),
        # so we use real instances. If these were remote services or APIs, we should mock
        # them to avoid external dependencies and keep tests fast and reliable.
        app.state.services = SimpleNamespace(
            password_hasher=BcryptPasswordHasher(),
            email_service=LoggerEmailService(),
        )


@pytest.fixture
async def async_client(
    db_pool: None,  # Ensures pool is initialized before client
) -> AsyncGenerator[AsyncClient]:
    """Provide an async HTTP client for testing FastAPI endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
