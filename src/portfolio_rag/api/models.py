"""HTTP transport models for the message API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageRequest(BaseModel):
    """Validated request to answer one user message.

    Attributes:
        message:
            User message for the current turn, limited to 2,048 characters.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    message: str = Field(
        min_length=1,
        max_length=2048,
        description="User message for the current turn, limited to 2,048 characters.",
    )

    @field_validator("message")
    @classmethod
    def message_must_contain_text(cls, value: str) -> str:
        """Reject messages containing only whitespace."""
        if not value.strip():
            raise ValueError("message must contain non-whitespace text")
        return value


class MessageResponse(BaseModel):
    """API response for one user message.

    Attributes:
        answer:
            User-visible answer produced by the use case.
        is_placeholder:
            Signals that the response is not a factual portfolio answer.
        correlation_id:
            Opaque identifier for tracing this request across processes.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    answer: str = Field(description="User-visible answer produced by the use case.")
    is_placeholder: Literal[True] = Field(
        description="Signals that the response is not a factual portfolio answer."
    )
    correlation_id: str = Field(
        min_length=1,
        max_length=64,
        description="Opaque identifier for tracing this request across processes.",
    )


class HealthResponse(BaseModel):
    """Bounded process-health response.

    Attributes:
        status:
            Whether the process can serve traffic.
        service:
            Stable identity of the responding process.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: Literal["ok", "unavailable"] = Field(
        description="Whether the process can serve traffic."
    )
    service: str = Field(description="Stable identity of the responding process.")


class ErrorResponse(BaseModel):
    """Safe error response without internal diagnostic details.

    Attributes:
        code:
            Stable machine-readable error category.
        message:
            Bounded user-safe explanation.
        correlation_id:
            Opaque identifier for correlating the failed request.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(description="Stable machine-readable error category.")
    message: str = Field(description="Bounded user-safe explanation.")
    correlation_id: str = Field(
        min_length=1,
        max_length=64,
        description="Opaque identifier for correlating the failed request.",
    )
