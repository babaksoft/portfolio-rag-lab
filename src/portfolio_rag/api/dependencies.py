"""FastAPI dependency accessors for composed application objects."""

from typing import cast

from fastapi import Request

from portfolio_rag.api.readiness import ReadinessProbe
from portfolio_rag.api.settings import ApiSettings
from portfolio_rag.application.services import AnswerMessageService


def get_api_settings(request: Request) -> ApiSettings:
    """Return settings installed by the API composition root."""
    return cast(ApiSettings, request.app.state.settings)


def get_answer_message_service(request: Request) -> AnswerMessageService:
    """Return the message service installed by the API composition root."""
    return cast(AnswerMessageService, request.app.state.answer_message_service)


def get_readiness_probe(request: Request) -> ReadinessProbe:
    """Return the required-dependency probe installed at composition."""
    return cast(ReadinessProbe, request.app.state.readiness_probe)
