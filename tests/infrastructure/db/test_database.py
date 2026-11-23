import asyncio
import os

import pytest
from sqlalchemy import text

from portfolio_rag.domain import AuthenticatedPrincipal
from portfolio_rag.infrastructure.db import Database, DbIdentityResolver

TEST_DATABASE_URL_VARIABLE = "PORTFOLIO_RAG_TEST_DATABASE_URL"


@pytest.mark.integration
def test_migrated_database_is_ready_and_has_pgvector() -> None:
    database_url = os.getenv(TEST_DATABASE_URL_VARIABLE)
    if database_url is None:
        pytest.skip(f"{TEST_DATABASE_URL_VARIABLE} is not configured")

    async def verify_database() -> None:
        database = Database(database_url, connection_timeout_seconds=2.0)
        try:
            assert await database.is_ready()
            async with database.sessions() as session:
                extension = await session.scalar(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                )
            assert extension == "vector"

            resolver = DbIdentityResolver(database.sessions)
            first = await resolver.execute(
                AuthenticatedPrincipal(
                    external_subject="integration-subject",
                    email="first@example.com",
                )
            )
            second = await resolver.execute(
                AuthenticatedPrincipal(
                    external_subject="integration-subject",
                    email="updated@example.com",
                )
            )
            assert second.id == first.id
            assert second.email == "updated@example.com"
        finally:
            await database.dispose()

    asyncio.run(verify_database())
