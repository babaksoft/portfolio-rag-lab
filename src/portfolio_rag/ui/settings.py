"""Typed configuration for the Streamlit process."""

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UiSettings(BaseSettings):
    """Environment-backed UI process settings."""

    model_config = SettingsConfigDict(
        env_prefix="PORTFOLIO_RAG_UI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base_url: AnyHttpUrl = Field(
        default=AnyHttpUrl("http://127.0.0.1:8000"),
        description="Base HTTP URL of the FastAPI backend used by the UI process.",
    )
    api_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
        le=30,
        description="Maximum time in seconds allowed for one backend API request.",
    )
