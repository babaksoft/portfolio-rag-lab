"""Operational readiness contract for the API adapter."""

from typing import Protocol


class ReadinessProbe(Protocol):
    """Check whether a required runtime dependency can serve requests."""

    async def is_ready(self) -> bool:
        """Return whether the dependency is currently available."""
