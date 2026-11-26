"""Typed configuration for the API process."""

from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """Environment-backed API process settings.

    Attributes:
        service_name:
            Stable service identity used by the API process.
        database_url:
            Optional complete asynchronous SQLAlchemy URL. When absent, the
            database component settings are assembled into a URL.
        database_host:
            PostgreSQL network hostname.
        database_port:
            PostgreSQL network port.
        database_name:
            PostgreSQL database name.
        database_username:
            PostgreSQL login role.
        database_password:
            PostgreSQL login password.
        database_connection_timeout_seconds:
            Maximum seconds allowed for database connection attempts.
        authentication_mode:
            Credential verification mode; disabled is only for local development.
        aws_region:
            AWS region containing the trusted ALB and Cognito user pool.
        alb_arn:
            Exact load balancer ARN accepted as an identity-assertion signer.
        cognito_user_pool_id:
            Cognito user pool whose signed access tokens are accepted.
        cognito_client_id:
            Cognito app client used by the ALB authentication action.
        authorized_group:
            Cognito group required for application access.
        cognito_domain:
            Cognito managed-login domain used for sign-out.
        application_url:
            Public application URL allowed as the Cognito logout destination.
        log_level:
            Minimum severity emitted by application structured logging.
    """

    model_config = SettingsConfigDict(
        env_prefix="PORTFOLIO_RAG_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    service_name: str = Field(
        default="portfolio-rag-api",
        min_length=1,
        max_length=64,
        description="Stable service identity used by the API process.",
    )
    database_url: SecretStr | None = Field(
        default=None,
        description=(
            "Optional complete asynchronous SQLAlchemy PostgreSQL URL; takes "
            "precedence over database component settings and is never returned by the API."
        ),
    )
    database_host: str = Field(
        default="127.0.0.1",
        min_length=1,
        max_length=253,
        description="PostgreSQL hostname used when database_url is absent.",
    )
    database_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="PostgreSQL TCP port used when database_url is absent.",
    )
    database_name: str = Field(
        default="portfolio_rag",
        min_length=1,
        max_length=64,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
        description="PostgreSQL database name used when database_url is absent.",
    )
    database_username: str = Field(
        default="portfolio_rag",
        min_length=1,
        max_length=64,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
        description="PostgreSQL login role used when database_url is absent.",
    )
    database_password: SecretStr = Field(
        default=SecretStr("portfolio_rag"),
        description=(
            "PostgreSQL password used when database_url is absent; injected from "
            "Secrets Manager in AWS and never returned by the API."
        ),
    )
    database_connection_timeout_seconds: float = Field(
        default=2.0,
        gt=0,
        le=10,
        description="Maximum seconds allowed for database connection attempts.",
    )
    authentication_mode: Literal["disabled", "alb_cognito"] = Field(
        default="disabled",
        description=(
            "Credential verification mode; disabled permits local development only, "
            "while alb_cognito verifies production edge and access tokens."
        ),
    )
    aws_region: str = Field(
        default="us-east-1",
        min_length=1,
        max_length=32,
        description="AWS region containing the trusted ALB and Cognito user pool.",
    )
    alb_arn: str | None = Field(
        default=None,
        max_length=2048,
        description="Exact trusted ALB signer ARN; required for alb_cognito mode.",
    )
    cognito_user_pool_id: str | None = Field(
        default=None,
        max_length=128,
        description="Trusted Cognito user pool ID; required for alb_cognito mode.",
    )
    cognito_client_id: str | None = Field(
        default=None,
        max_length=128,
        description="Trusted Cognito app client ID; required for alb_cognito mode.",
    )
    authorized_group: str = Field(
        default="reviewers",
        min_length=1,
        max_length=128,
        description="Exact Cognito group required for protected API operations.",
    )
    cognito_domain: str | None = Field(
        default=None,
        max_length=253,
        description="Cognito managed-login hostname; required for production sign-out.",
    )
    application_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Public HTTPS application URL used after Cognito sign-out.",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Minimum severity emitted by application structured logging.",
    )

    @model_validator(mode="after")
    def validate_authentication_configuration(self) -> Self:
        """Require every trust anchor when production authentication is enabled."""
        if self.authentication_mode == "alb_cognito" and any(
            value is None
            for value in (
                self.alb_arn,
                self.cognito_user_pool_id,
                self.cognito_client_id,
                self.cognito_domain,
                self.application_url,
            )
        ):
            raise ValueError(
                "alb_arn, cognito_user_pool_id, and cognito_client_id are required "
                "for alb_cognito authentication"
            )
        return self
