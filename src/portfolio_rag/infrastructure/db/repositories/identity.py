"""PostgreSQL-backed identity persistence adapters."""

from collections.abc import Callable
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from portfolio_rag.application.services import ResolveIdentityService
from portfolio_rag.domain import AuthenticatedPrincipal, Identity
from portfolio_rag.infrastructure.db.models import IdentityModel


class DbIdentityRepository:
    """Resolve identities within a caller-owned database transaction."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with its transaction-scoped session."""
        self._session = session

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
        model = (await self._session.execute(statement)).scalar_one()
        return Identity(
            id=model.id,
            external_subject=model.external_subject,
            email=model.email,
        )


class DbIdentityResolver:
    """Run identity resolution in a short, adapter-owned transaction."""

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        """Initialize the resolver from the process-owned session factory."""
        self._session_factory = session_factory

    async def execute(self, principal: AuthenticatedPrincipal) -> Identity:
        """Resolve and commit one identity transaction."""
        async with self._session_factory() as session:
            service = ResolveIdentityService(DbIdentityRepository(session))
            identity = await service.execute(principal)
            await session.commit()
        return identity
