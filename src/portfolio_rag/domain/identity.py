"""Identity values used by authorization and application behavior."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedPrincipal(BaseModel):
    """Verified external identity presented to the application.

    Attributes:
        external_subject:
            Stable subject from the configured Cognito user pool.
        email:
            Optional verified profile email supplied by Cognito.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    external_subject: str = Field(
        min_length=1,
        max_length=128,
        description="Stable subject from the verified Cognito credentials.",
    )
    email: str | None = Field(
        default=None,
        max_length=320,
        description="Verified profile email supplied by Cognito when available.",
    )


class Identity(BaseModel):
    """Stable internal identity resolved from an external principal.

    Attributes:
        id:
            Application-owned identifier that remains stable across sessions.
        external_subject:
            Unique Cognito subject used only for identity reconciliation.
        email:
            Most recently observed verified profile email, when available.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID = Field(description="Application-owned stable identity identifier.")
    external_subject: str = Field(
        min_length=1,
        max_length=128,
        description="Unique Cognito subject used to reconcile future sessions.",
    )
    email: str | None = Field(
        default=None,
        max_length=320,
        description="Most recently observed verified profile email, when available.",
    )
