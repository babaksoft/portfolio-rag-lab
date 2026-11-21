"""Typed configuration for the API process."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


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

    def resolved_database_url(self) -> str:
        """Return the configured or safely assembled SQLAlchemy database URL."""
        if self.database_url is not None:
            return self.database_url.get_secret_value()

        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.database_username,
            password=self.database_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        ).render_as_string(hide_password=False)
