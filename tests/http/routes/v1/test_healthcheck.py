from fastapi import status
from httpx import AsyncClient


async def test_healthcheck_endpoint(async_client: AsyncClient) -> None:
    """Test the healthcheck endpoint returns a successful response with correct structure."""
    response = await async_client.get("/v1/healthcheck")

    assert response.status_code == status.HTTP_200_OK
    data: dict[str, str] = response.json()

    # Verify all required fields are present
    assert "status" in data
    assert "timestamp" in data
    assert "message" in data

    # Verify field values
    assert data["status"] == "ok"
    assert data["message"] == "Service is healthy"

    # Verify timestamp is a valid ISO format string
    assert isinstance(data["timestamp"], str)
    assert "T" in data["timestamp"] or "Z" in data["timestamp"]
