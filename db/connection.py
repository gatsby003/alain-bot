"""Database connection management with asyncpg."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg


class Database:
    """Async PostgreSQL connection pool manager."""

    _pool: asyncpg.Pool | None = None

    @classmethod
    async def connect(cls, dsn: str | None = None) -> None:
        """Initialize the connection pool."""
        if cls._pool is not None:
            return

        dsn = dsn or os.getenv("DATABASE_URL")
        if not dsn:
            raise ValueError("DATABASE_URL environment variable not set")

        cls._pool = await asyncpg.create_pool(
            dsn,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )

    @classmethod
    async def disconnect(cls) -> None:
        """Close the connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    def get_pool(cls) -> asyncpg.Pool:
        """Get the connection pool."""
        if cls._pool is None:
            raise RuntimeError("Database not connected. Call Database.connect() first.")
        return cls._pool

    @classmethod
    @asynccontextmanager
    async def acquire(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection from the pool."""
        pool = cls.get_pool()
        async with pool.acquire() as conn:
            yield conn

    @classmethod
    @asynccontextmanager
    async def transaction(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection with a transaction."""
        async with cls.acquire() as conn:
            async with conn.transaction():
                yield conn

