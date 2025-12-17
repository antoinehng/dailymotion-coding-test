"""Authentication dependencies for FastAPI endpoints."""

from fastapi import HTTPException
from fastapi import Request
from fastapi import Security
from fastapi import status
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials

from src.domain.user.entities.user import User
from src.domain.user.errors import UserNotFoundError
from src.domain.user.value_objects.password import Password
from src.http.dependencies.database_asyncpg import DbConnection
from src.infrastructure.database.postgres.repositories.user_repository import (
    PostgresUserRepository,
)

# Create HTTPBasic security scheme
security_scheme = HTTPBasic()


async def get_authenticated_user_from_basic_auth(
    credentials: HTTPBasicCredentials = Security(security_scheme),
    request: Request = None,  # type: ignore[assignment]
    conn: DbConnection = None,  # type: ignore[assignment]
) -> User:
    """Extract and validate user credentials from Basic Auth (email:password).

    Basic Auth format: Authorization: Basic <base64(email:password)>
    FastAPI automatically decodes the Base64 credentials for us.

    Args:
        credentials: HTTP Basic Auth credentials from Authorization header
        request: FastAPI request object to access app state (injected via dependency)
        conn: Database connection from the pool (injected via dependency)

    Returns:
        UserPublicId of the authenticated user

    Raises:
        HTTPException: If credentials are invalid or user not found
    """
    email = credentials.username
    password = credentials.password

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Get user repository and password hasher
    user_repository = PostgresUserRepository(conn)
    password_hasher = request.app.state.services.password_hasher

    try:
        # Find user by email
        user = await user_repository.find_by_email(email)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Basic"},
        ) from None

    # Verify password
    try:
        password_vo = Password(password)
        is_valid = password_hasher.verify(password_vo, user.password_hash)
    except (ValueError, ExceptionGroup):
        # Password validation failed (invalid format)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Basic"},
        ) from None

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user
