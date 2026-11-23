import asyncio
from uuid import UUID

from portfolio_rag.application.services import ResolveIdentityService
from portfolio_rag.domain import AuthenticatedPrincipal, Identity


class _IdentityRepository:
    def __init__(self) -> None:
        self.principal: AuthenticatedPrincipal | None = None

    async def resolve(self, principal: AuthenticatedPrincipal) -> Identity:
        self.principal = principal
        return Identity(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            external_subject=principal.external_subject,
            email=principal.email,
        )


def test_resolves_verified_principal_through_repository() -> None:
    repository = _IdentityRepository()
    service = ResolveIdentityService(repository)
    principal = AuthenticatedPrincipal(
        external_subject="stable-subject",
        email="reviewer@example.com",
    )

    identity = asyncio.run(service.execute(principal))

    assert repository.principal == principal
    assert identity.external_subject == "stable-subject"
