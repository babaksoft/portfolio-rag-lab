"""FastAPI composition root."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from portfolio_rag.api.correlation import propagate_correlation_id
from portfolio_rag.api.errors import handle_validation_error
from portfolio_rag.api.readiness import ReadinessProbe
from portfolio_rag.api.routes import health_router, messages_router
from portfolio_rag.api.settings import ApiSettings
from portfolio_rag.application.services import AnswerMessageService
from portfolio_rag.infrastructure.db import Database


def create_app(
    settings: ApiSettings | None = None,
    readiness_probe: ReadinessProbe | None = None,
) -> FastAPI:
    """Create the API application with its process-level dependencies.

    Args:
        settings:
            Optional settings override used by tests and alternate runtimes.
        readiness_probe:
            Optional required-dependency probe used by boundary tests.

    Returns:
        Configured FastAPI application.
    """
    api_settings = settings or ApiSettings()
    database = None
    if readiness_probe is None:
        database = Database(
            api_settings.resolved_database_url(),
            connection_timeout_seconds=(
                api_settings.database_connection_timeout_seconds
            ),
        )
        readiness_probe = database

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncGenerator[None, None]:
        """Release process-owned database connections on shutdown."""
        try:
            yield
        finally:
            if database is not None:
                await database.dispose()

    application = FastAPI(
        title="Portfolio Retrieval Lab API",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.state.settings = api_settings
    application.state.answer_message_service = AnswerMessageService()
    application.state.readiness_probe = readiness_probe

    application.middleware("http")(propagate_correlation_id)
    application.add_exception_handler(RequestValidationError, handle_validation_error)

    application.include_router(health_router)
    application.include_router(messages_router)

    return application


app = create_app()
