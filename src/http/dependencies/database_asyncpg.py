"""FastAPI dependencies for AsyncPG database connection.

This module provides FastAPI dependencies for accessing the database connection pool
using asyncpg.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

import asyncpg
from asyncpg.pool import PoolConnectionProxy
from fastapi import Depends
from fastapi import Request


async def get_db_connection(
    request: Request,
) -> AsyncGenerator[PoolConnectionProxy]:
    """Get a database connection from the pool.

    This dependency acquires a connection from the pool and automatically
    returns it when the request is done.

    Args:
        request: FastAPI request object.

    Yields:
        A database connection from the pool.

    Example:
        @router.get("/users")
        async def get_users(conn: asyncpg.Connection = Depends(get_db_connection)):
            users = await conn.fetch("SELECT * FROM users")
            return users
    """
    pool: asyncpg.Pool = request.app.state.db_pool.pool
    async with pool.acquire() as connection:
        yield connection


# Type alias for easier use in route handlers
# PoolConnectionProxy is compatible with Connection for all practical purposes
DbConnection = Annotated[PoolConnectionProxy, Depends(get_db_connection)]
