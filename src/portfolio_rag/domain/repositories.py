"""Repository contracts owned by the domain boundary."""

from typing import Protocol

from portfolio_rag.domain.identity import AuthenticatedPrincipal, Identity


class IdentityRepository(Protocol):
    """Persist and retrieve stable internal identities."""

    async def resolve(self, principal: AuthenticatedPrincipal) -> Identity:
        """Return the stable identity for a verified external principal."""
        ...
