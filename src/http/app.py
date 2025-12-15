from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from src.http.middlewares import LoggingMiddleware
from src.http.routes import router

"""
# FastAPI App
"""


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # App startup

    fastapi_app.state.services = {}

    yield  # App Running

    # App Shutdown
    del fastapi_app.state.services


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
                "url": "http://localhost:8000",
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
