from pydantic import SecretStr

from portfolio_rag.api.settings import ApiSettings


def test_database_url_override_takes_precedence() -> None:
    settings = ApiSettings(
        database_url=SecretStr("postgresql+asyncpg://override:secret@db/example"),
        database_host="ignored",
    )

    assert (
        settings.resolved_database_url()
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

    assert settings.resolved_database_url() == (
        "postgresql+asyncpg://portfolio_admin:p%40ss%2Fword@"
        "database.internal:5433/portfolio_rag"
    )
