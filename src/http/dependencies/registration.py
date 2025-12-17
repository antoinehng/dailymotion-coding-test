from fastapi import Request

from src.application.registration.use_cases.activate_user import ActivateUser
from src.application.registration.use_cases.issue_activation_code import (
    IssueActivationCode,
)
from src.application.registration.use_cases.register_user import RegisterUser
from src.http.dependencies.database_asyncpg import DbConnection
from src.infrastructure.database.postgres.repositories.activation_code_repository import (
    PostgresActivationCodeRepository,
)
from src.infrastructure.database.postgres.repositories.user_repository import (
    PostgresUserRepository,
)


def get_register_user_use_case(
    request: Request,
    conn: DbConnection,
) -> RegisterUser:
    """Dependency to create RegisterUser use case with all dependencies.

    Args:
        request: FastAPI request object to access app state
        conn: Database connection from the pool

    Returns:
        RegisterUser use case instance
    """
    user_repository = PostgresUserRepository(conn)
    password_hasher = request.app.state.services.password_hasher

    return RegisterUser(
        user_repository=user_repository,
        password_hasher=password_hasher,
    )


def get_activate_user_use_case(
    request: Request,
    conn: DbConnection,
) -> ActivateUser:
    """Dependency to create ActivateUser use case with all dependencies.

    Args:
        request: FastAPI request object to access app state
        conn: Database connection from the pool

    Returns:
        ActivateUser use case instance
    """
    user_repository = PostgresUserRepository(conn)
    activation_code_repository = PostgresActivationCodeRepository(conn)

    return ActivateUser(
        user_repository=user_repository,
        activation_code_repository=activation_code_repository,
    )


def get_issue_activation_code_use_case(
    request: Request,
    conn: DbConnection,
) -> IssueActivationCode:
    """Dependency to create IssueActivationCode use case with all dependencies.

    Args:
        request: FastAPI request object to access app state
        conn: Database connection from the pool

    Returns:
        IssueActivationCode use case instance
    """
    user_repository = PostgresUserRepository(conn)
    activation_code_repository = PostgresActivationCodeRepository(conn)
    email_service = request.app.state.services.email_service

    return IssueActivationCode(
        user_repository=user_repository,
        activation_code_repository=activation_code_repository,
        email_service=email_service,
    )
