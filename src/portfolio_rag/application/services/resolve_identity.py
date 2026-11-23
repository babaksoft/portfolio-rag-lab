"""Resolve a verified external principal to an internal identity."""

from portfolio_rag.domain import AuthenticatedPrincipal, Identity, IdentityRepository


class ResolveIdentityService:
    """Resolve one verified principal through the identity repository."""

    def __init__(self, repository: IdentityRepository) -> None:
        """Initialize the service with its persistence boundary."""
        self._repository = repository

    async def execute(self, principal: AuthenticatedPrincipal) -> Identity:
        """Return the stable internal identity for the verified principal."""
        return await self._repository.resolve(principal)
