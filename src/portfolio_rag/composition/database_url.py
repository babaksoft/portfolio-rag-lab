"""Resolve the database connection configuration for the API and migrations."""

from sqlalchemy.engine import URL

from portfolio_rag.api import ApiSettings


def resolve_database_url(settings: ApiSettings) -> str:
    """Return the configured or safely assembled SQLAlchemy database URL.

    Args:
        settings:
            Environment-backed settings for the API database.

    Returns:
        Connection URL for the asynchronous PostgreSQL engine.
    """
    if settings.database_url is not None:
        return settings.database_url.get_secret_value()

    return URL.create(
        drivername="postgresql+asyncpg",
        username=settings.database_username,
        password=settings.database_password.get_secret_value(),
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
    ).render_as_string(hide_password=False)
