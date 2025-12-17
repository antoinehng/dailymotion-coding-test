from contextlib import asynccontextmanager
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from src.http.middlewares import LoggingMiddleware
from src.http.routes import router
from src.infrastructure.database.postgres.asyncpg_pool import close_db_pool
from src.infrastructure.database.postgres.asyncpg_pool import initialize_db_pool
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.infrastructure.smtp.email_service import LoggerEmailService

"""
# FastAPI App
"""


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # App startup
    await initialize_db_pool(
        app=fastapi_app,
        min_size=10,  # Minimum connections in pool
        max_size=20,  # Maximum connections in pool
    )

    # Initialize services once
    fastapi_app.state.services = SimpleNamespace(
        password_hasher=BcryptPasswordHasher(),
        email_service=LoggerEmailService(),
    )

    yield  # App Running

    # App Shutdown
    await close_db_pool()


app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    title="Dailymotion Coding Test",
    contact={
        "email": "antoinehng@proton.me",
    },
    servers=[
        (
            {
                "url": "http://localhost:8080",
                "description": "Local development server",
            }
        ),
    ],
)

"""
# Middlewares

The order of middleware execution in FastAPI follows a "first in, last out" (FILO) approach.
This means that the first middleware registered will be the last one to execute, and the last middleware registered will be the first one to execute.
"""
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    GZipMiddleware,
    minimum_size=500,  # Compress responses larger than 500 bytes
)

"""
# Routers
"""
app.include_router(router)

"""
# Exception Handlers

FastAPI will check the exception handlers in the order they are defined and execute the first one that matches the exception type.
More specific exception handlers should be defined before more general ones to ensure that the correct handler is executed for each exception type.
"""
app.exception_handlers = {}

"""
# Swagger UI Parameters

https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration
"""
app.swagger_ui_parameters = {
    "defaultModelsExpandDepth": 0,  # Do not expand models by default
    "displayRequestDuration": True,  # Show request duration
    "filter": True,  # Enable filtering
    "persistAuthorization": True,  # Keep auth token on browser refresh
    "showExtensions": True,  # Show vendor extensions such as x-auth-token
    "tryItOutEnabled": True,  # Enable the "Try it out" button by default
}
