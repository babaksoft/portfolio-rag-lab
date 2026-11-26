"""FastAPI setup for the HTTP adapter."""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from portfolio_rag.api.correlation import propagate_correlation_id
from portfolio_rag.api.errors import (
    AccessDeniedError,
    handle_access_denied,
    handle_validation_error,
)
from portfolio_rag.api.readiness import ReadinessProbe
from portfolio_rag.api.routes import auth_router, health_router, messages_router
from portfolio_rag.api.settings import ApiSettings
from portfolio_rag.application import IdentityResolver, IdentityVerifier
from portfolio_rag.application.services import AnswerMessageService


def build_app(
    *,
    settings: ApiSettings,
    answer_message_service: AnswerMessageService,
    readiness_probe: ReadinessProbe,
    identity_verifier: IdentityVerifier | None,
    identity_resolver: IdentityResolver | None,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]],
) -> FastAPI:
    """Register the HTTP boundary with its supplied dependencies.

    Args:
        settings:
            Settings used by the HTTP adapter.
        answer_message_service:
            Use case that handles submitted messages.
        readiness_probe:
            Probe for dependencies required to serve requests.
        identity_verifier:
            Credential verifier used when authentication is enabled.
        identity_resolver:
            Internal identity resolver used when authentication is enabled.
        lifespan:
            Context manager for the process-owned dependencies.

    Returns:
        Configured FastAPI application.
    """
    application = FastAPI(
        title="Portfolio Retrieval Lab API",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.state.settings = settings
    application.state.answer_message_service = answer_message_service
    application.state.readiness_probe = readiness_probe
    application.state.identity_verifier = identity_verifier
    application.state.identity_resolver = identity_resolver

    application.middleware("http")(propagate_correlation_id)
    application.add_exception_handler(RequestValidationError, handle_validation_error)
    application.add_exception_handler(AccessDeniedError, handle_access_denied)

    application.include_router(auth_router)
    application.include_router(health_router)
    application.include_router(messages_router)

    return application
