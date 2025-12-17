from src.application.registration.use_cases.register_user import RegisterUser
from src.http.dependencies.database_asyncpg import DbConnection
from src.infrastructure.database.postgres.repositories.activation_code_repository import (
    PostgresActivationCodeRepository,
)
from src.infrastructure.database.postgres.repositories.user_repository import (
    PostgresUserRepository,
)
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.infrastructure.smtp.email_service import LoggerEmailService


def get_register_user_use_case(
    conn: DbConnection,
) -> RegisterUser:
    """Dependency to create RegisterUser use case with all dependencies.

    Args:
        conn: Database connection from the pool

    Returns:
        RegisterUser use case instance
    """
    user_repository = PostgresUserRepository(conn)
    activation_code_repository = PostgresActivationCodeRepository(conn)
    password_hasher = BcryptPasswordHasher()
    email_service = LoggerEmailService()

    return RegisterUser(
        user_repository=user_repository,
        password_hasher=password_hasher,
        email_service=email_service,
        activation_code_repository=activation_code_repository,
    )
