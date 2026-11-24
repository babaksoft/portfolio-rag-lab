"""Typed task-oriented HTTP client owned by the Streamlit adapter."""

from typing import Literal
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from portfolio_rag.ui.settings import UiSettings

CORRELATION_HEADER = "X-Correlation-ID"
IDENTITY_ASSERTION_HEADER = "X-Amzn-Oidc-Data"
ACCESS_TOKEN_HEADER = "X-Amzn-Oidc-AccessToken"


class _MessagePayload(BaseModel):
    """Serialized backend request payload."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    message: str = Field(description="User message sent to the backend.")


class MessageResult(BaseModel):
    """Validated message result exposed to Streamlit rendering code.

    Attributes:
        answer:
            User-visible answer returned by the backend.
        is_placeholder:
            Whether the answer is the non-factual Phase 0 placeholder.
        correlation_id:
            Opaque identifier tracing the request across processes.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    answer: str = Field(description="User-visible answer returned by the backend.")
    is_placeholder: Literal[True] = Field(
        description="Whether the answer is the non-factual Phase 0 placeholder."
    )
    correlation_id: str = Field(
        min_length=1,
        max_length=64,
        description="Opaque identifier tracing the request across processes.",
    )


class ApiClientError(Exception):
    """Bounded backend failure safe to present in the UI."""

    def __init__(self, code: str, user_message: str) -> None:
        """Initialize an error category and its safe presentation text."""
        super().__init__(user_message)
        self.code = code
        self.user_message = user_message


class PortfolioApiClient:
    """Call typed Portfolio Retrieval Lab backend operations."""

    def __init__(
        self,
        settings: UiSettings,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Initialize the client from process settings and an optional transport."""
        self._base_url = str(settings.api_base_url).rstrip("/")
        self._timeout_seconds = settings.api_timeout_seconds
        self._transport = transport

    def answer_message(
        self,
        message: str,
        correlation_id: str | None = None,
        *,
        identity_assertion: str | None = None,
        access_token: str | None = None,
    ) -> MessageResult:
        """Ask the backend to answer one message.

        Args:
            message:
                User message to send to the backend.
            correlation_id:
                Optional caller-provided trace identifier.
            identity_assertion:
                Signed ALB user-claims assertion received by Streamlit.
            access_token:
                Signed Cognito access token received through the ALB.

        Returns:
            Validated task-oriented response.

        Raises:
            ApiClientError:
                If the backend is unavailable or violates its contract.
        """
        request_correlation_id = correlation_id or str(uuid4())
        payload = _MessagePayload(message=message)
        headers = {CORRELATION_HEADER: request_correlation_id}
        if identity_assertion is not None:
            headers[IDENTITY_ASSERTION_HEADER] = identity_assertion
        if access_token is not None:
            headers[ACCESS_TOKEN_HEADER] = access_token

        try:
            with httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = client.post(
                    "/v1/messages",
                    json=payload.model_dump(mode="json"),
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.RequestError as error:
            raise ApiClientError(
                "backend_unavailable",
                "The assistant is temporarily unavailable. Please try again.",
            ) from error
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 401:
                raise ApiClientError(
                    "authentication_required",
                    "We could not verify your session. Sign out, then sign in again. "
                    "If the problem continues, contact the application owner.",
                ) from error
            if error.response.status_code == 403:
                raise ApiClientError(
                    "access_denied",
                    "Access denied. Your account is not authorized as a reviewer. "
                    "Contact the application owner if you need access.",
                ) from error
            code = (
                "invalid_request" if error.response.is_client_error else "backend_error"
            )
            raise ApiClientError(
                code,
                "The assistant could not process that request. Please try again.",
            ) from error

        try:
            return MessageResult.model_validate(response.json())
        except (ValueError, ValidationError) as error:
            raise ApiClientError(
                "invalid_backend_response",
                "The assistant returned an invalid response. Please try again.",
            ) from error
