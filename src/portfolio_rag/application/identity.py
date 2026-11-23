"""Application ports and failures for verified identity resolution."""

from typing import Protocol

from portfolio_rag.domain import AuthenticatedPrincipal, Identity


class AuthenticationError(Exception):
    """Credentials are absent, invalid, expired, or internally inconsistent."""


class AuthorizationError(Exception):
    """A verified principal lacks required application access."""


class IdentityVerifier(Protocol):
    """Verify boundary credentials and enforce the configured access group."""

    async def verify(
        self, identity_assertion: str, access_token: str
    ) -> AuthenticatedPrincipal:
        """Return a principal only after both credentials are verified."""
        ...


class IdentityResolver(Protocol):
    """Resolve a verified principal to a stable internal identity."""

    async def execute(self, principal: AuthenticatedPrincipal) -> Identity:
        """Return the stable identity for the verified principal."""
        ...
