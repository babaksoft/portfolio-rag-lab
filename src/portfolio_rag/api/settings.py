"""Typed configuration for the API process."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """Environment-backed API process settings.

    Attributes:
        service_name:
            Stable service identity used by the API process.
        database_url:
            Asynchronous SQLAlchemy URL for the required PostgreSQL database.
        database_connection_timeout_seconds:
            Maximum seconds allowed for database connection attempts.
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
    database_url: SecretStr = Field(
        default=SecretStr(
            "postgresql+asyncpg://portfolio_rag:portfolio_rag@127.0.0.1:5432/portfolio_rag"
        ),
        description=(
            "Asynchronous SQLAlchemy PostgreSQL URL; injected as a secret in "
            "deployed environments and never returned by the API."
        ),
    )
    database_connection_timeout_seconds: float = Field(
        default=2.0,
        gt=0,
        le=10,
        description="Maximum seconds allowed for database connection attempts.",
    )
