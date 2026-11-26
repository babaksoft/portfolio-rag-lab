"""PostgreSQL-backed identity repository."""

from collections.abc import Callable
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from portfolio_rag.domain import AuthenticatedPrincipal, Identity
from portfolio_rag.infrastructure.db.models import IdentityModel


class DbIdentityRepository:
    """Resolve identities in a short, repository-owned database transaction."""

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        """Initialize the repository with the process-owned session factory."""
        self._session_factory: Callable[[], AsyncSession] = session_factory

    async def resolve(self, principal: AuthenticatedPrincipal) -> Identity:
        """Create or refresh the identity for an external subject atomically."""
        statement = (
            insert(IdentityModel)
            .values(
                id=uuid4(),
                external_subject=principal.external_subject,
                email=principal.email,
            )
            .on_conflict_do_update(
                index_elements=[IdentityModel.external_subject],
                set_={"email": principal.email, "updated_at": func.now()},
            )
            .returning(IdentityModel)
        )
        async with self._session_factory() as session:
            model = (await session.execute(statement)).scalar_one()
            identity = Identity(
                id=model.id,
                external_subject=model.external_subject,
                email=model.email,
            )
            await session.commit()

        return identity
