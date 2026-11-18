"""FastAPI composition root."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from portfolio_rag.api.correlation import propagate_correlation_id
from portfolio_rag.api.errors import handle_validation_error
from portfolio_rag.api.routes.health import router as health_router
from portfolio_rag.api.routes.messages import router as messages_router
from portfolio_rag.api.settings import ApiSettings
from portfolio_rag.application.services import AnswerMessageService


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Create the API application with its process-level dependencies.

    Args:
        settings: Optional settings override used by tests and alternate runtimes.

    Returns:
        Configured FastAPI application.
    """
    api_settings = settings or ApiSettings()
    application = FastAPI(title="Portfolio Retrieval Lab API")

    application.state.settings = api_settings
    application.state.answer_message_service = AnswerMessageService()
    application.middleware("http")(propagate_correlation_id)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.include_router(health_router)
    application.include_router(messages_router)

    return application


app = create_app()
