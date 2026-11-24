"""FastAPI dependency accessors for composed application objects."""

import logging
from typing import cast
from uuid import UUID

from fastapi import Header, Request

from portfolio_rag.api.errors import AccessDeniedError
from portfolio_rag.api.readiness import ReadinessProbe
from portfolio_rag.api.settings import ApiSettings
from portfolio_rag.application import (
    AuthenticationError,
    AuthorizationError,
    IdentityResolver,
    IdentityVerifier,
)
from portfolio_rag.application.services import AnswerMessageService
from portfolio_rag.domain import Identity

logger = logging.getLogger(__name__)


def get_api_settings(request: Request) -> ApiSettings:
    """Return settings installed by the API composition root."""
    return cast(ApiSettings, request.app.state.settings)


def get_answer_message_service(request: Request) -> AnswerMessageService:
    """Return the message service installed by the API composition root."""
    return cast(AnswerMessageService, request.app.state.answer_message_service)


def get_readiness_probe(request: Request) -> ReadinessProbe:
    """Return the required-dependency probe installed at composition."""
    return cast(ReadinessProbe, request.app.state.readiness_probe)


async def get_current_identity(
    request: Request,
    identity_assertion: str | None = Header(default=None, alias="X-Amzn-Oidc-Data"),
    access_token: str | None = Header(default=None, alias="X-Amzn-Oidc-AccessToken"),
) -> Identity:
    """Verify request credentials and resolve the stable internal identity."""
    settings = get_api_settings(request)
    if settings.authentication_mode == "disabled":
        return Identity(
            id=UUID(int=0),
            external_subject="local-development",
            email=None,
        )

    if identity_assertion is None or access_token is None:
        logger.warning(
            "Authentication credentials missing",
            extra={
                "event": "authentication_missing",
                "error_code": "authentication_required",
            },
        )
        raise AccessDeniedError(
            status_code=401,
            code="authentication_required",
            message="Authentication is required.",
        )

    verifier = cast(IdentityVerifier, request.app.state.identity_verifier)
    resolver = cast(IdentityResolver, request.app.state.identity_resolver)
    try:
        principal = await verifier.verify(identity_assertion, access_token)
    except AuthenticationError as error:
        logger.warning(
            "Authentication verification failed",
            extra={
                "event": "authentication_failed",
                "error_code": "invalid_authentication",
            },
        )
        raise AccessDeniedError(
            status_code=401,
            code="invalid_authentication",
            message="Authentication could not be verified.",
        ) from error
    except AuthorizationError as error:
        logger.warning(
            "Authorization verification failed",
            extra={"event": "authorization_denied", "error_code": "access_denied"},
        )
        raise AccessDeniedError(
            status_code=403,
            code="access_denied",
            message="This account is not authorized.",
        ) from error

    logger.info("Authentication verified", extra={"event": "authentication_verified"})
    identity = await resolver.execute(principal)
    logger.info("Identity resolved", extra={"event": "identity_resolved"})
    return identity
