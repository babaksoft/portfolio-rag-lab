"""Public persistence-model boundary."""

from portfolio_rag.infrastructure.db.models.base import Base
from portfolio_rag.infrastructure.db.models.identity import IdentityModel

__all__ = ["Base", "IdentityModel"]
