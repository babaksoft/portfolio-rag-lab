"""Construct and manage the API runtime dependencies."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI

from portfolio_rag import configure_structured_logging
from portfolio_rag.api import ApiSettings, ReadinessProbe, build_app
from portfolio_rag.application import IdentityResolver, IdentityVerifier
from portfolio_rag.application.services import (
    AnswerMessageService,
    ResolveIdentityService,
)
from portfolio_rag.composition.database_url import resolve_database_url
from portfolio_rag.infrastructure.auth import AlbCognitoIdentityVerifier
from portfolio_rag.infrastructure.db import Database, DbIdentityRepository


@asynccontextmanager
async def _lifespan(
    application: FastAPI, *, database: Database | None
) -> AsyncGenerator[None, None]:
    """Release process-owned database connections on shutdown."""
    try:
        yield
    finally:
        if database is not None:
            await database.dispose()


def create_app(
    settings: ApiSettings | None = None,
    readiness_probe: ReadinessProbe | None = None,
    identity_verifier: IdentityVerifier | None = None,
    identity_resolver: IdentityResolver | None = None,
) -> FastAPI:
    """Create the API application with its process-level dependencies.

    Args:
        settings:
            Optional settings override used by tests and alternate runtimes.
        readiness_probe:
            Optional required-dependency probe used by boundary tests.
        identity_verifier:
            Optional credential verifier used by authentication boundary tests.
        identity_resolver:
            Optional internal identity resolver used by boundary tests.

    Returns:
        Configured FastAPI application.

    Raises:
        ValueError:
            Production authentication uses a custom probe without an identity resolver.
    """
    api_settings = settings or ApiSettings()
    configure_structured_logging(
        service=api_settings.service_name,
        level=api_settings.log_level,
    )
    database = None
    if readiness_probe is None:
        database = Database(
            resolve_database_url(api_settings),
            connection_timeout_seconds=(
                api_settings.database_connection_timeout_seconds
            ),
        )
        readiness_probe = database

    if api_settings.authentication_mode == "alb_cognito":
        if identity_verifier is None:
            assert api_settings.alb_arn is not None
            assert api_settings.cognito_user_pool_id is not None
            assert api_settings.cognito_client_id is not None
            identity_verifier = AlbCognitoIdentityVerifier(
                region=api_settings.aws_region,
                load_balancer_arn=api_settings.alb_arn,
                user_pool_id=api_settings.cognito_user_pool_id,
                client_id=api_settings.cognito_client_id,
                required_group=api_settings.authorized_group,
            )
        if identity_resolver is None:
            if database is None:
                raise ValueError(
                    "identity_resolver is required when a readiness probe replaces "
                    "the production database"
                )
            identity_resolver = ResolveIdentityService(
                DbIdentityRepository(database.sessions)
            )

    return build_app(
        settings=api_settings,
        answer_message_service=AnswerMessageService(),
        readiness_probe=readiness_probe,
        identity_verifier=identity_verifier,
        identity_resolver=identity_resolver,
        lifespan=partial(_lifespan, database=database),
    )
