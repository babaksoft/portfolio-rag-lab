"""Asynchronous SQLAlchemy database lifecycle."""

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Own the backend connection pool and transaction factory.

    Attributes:
        sessions:
            Factory for explicit asynchronous transaction scopes.
    """

    sessions: async_sessionmaker[AsyncSession]

    def __init__(
        self,
        url: str,
        *,
        connection_timeout_seconds: float,
    ) -> None:
        """Configure a lazy asynchronous database connection pool.

        Args:
            url:
                SQLAlchemy asynchronous PostgreSQL connection URL.
            connection_timeout_seconds:
                Maximum duration for connection and readiness attempts.
        """
        self._connection_timeout_seconds = connection_timeout_seconds
        self._engine: AsyncEngine = create_async_engine(
            url,
            pool_pre_ping=True,
            pool_timeout=connection_timeout_seconds,
            connect_args={"timeout": connection_timeout_seconds},
        )
        self.sessions = async_sessionmaker(
            self._engine,
            autoflush=False,
            expire_on_commit=False,
        )

    async def is_ready(self) -> bool:
        """Return whether PostgreSQL accepts a bounded probe query."""
        try:
            async with asyncio.timeout(self._connection_timeout_seconds):
                async with self._engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
        except Exception:  # Readiness must safely collapse adapter failures.
            return False

        return True

    async def dispose(self) -> None:
        """Close all pooled database connections during process shutdown."""
        await self._engine.dispose()
