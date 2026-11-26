import pytest
from pydantic import SecretStr, ValidationError

from portfolio_rag.api import ApiSettings
from portfolio_rag.composition import resolve_database_url


def test_database_url_override_takes_precedence() -> None:
    settings = ApiSettings(
        database_url=SecretStr("postgresql+asyncpg://override:secret@db/example"),
        database_host="ignored",
    )

    assert (
        resolve_database_url(settings)
        == "postgresql+asyncpg://override:secret@db/example"
    )


def test_database_components_are_safely_encoded() -> None:
    settings = ApiSettings(
        database_host="database.internal",
        database_port=5433,
        database_name="portfolio_rag",
        database_username="portfolio_admin",
        database_password=SecretStr("p@ss/word"),
    )

    assert resolve_database_url(settings) == (
        "postgresql+asyncpg://portfolio_admin:p%40ss%2Fword@"
        "database.internal:5433/portfolio_rag"
    )


def test_production_authentication_requires_every_trust_anchor() -> None:
    with pytest.raises(ValidationError, match="alb_arn"):
        ApiSettings(authentication_mode="alb_cognito")
