"""Typed configuration for the API process."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """Environment-backed API process settings."""

    model_config = SettingsConfigDict(
        env_prefix="PORTFOLIO_RAG_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = Field(
        default="portfolio-rag-api",
        min_length=1,
        max_length=64,
        description="Stable service identity used by the API process.",
    )
