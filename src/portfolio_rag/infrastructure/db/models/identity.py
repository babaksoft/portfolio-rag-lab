"""Mapped persistence model for internal identities."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from portfolio_rag.infrastructure.db.models.base import Base


class IdentityModel(Base):
    """Persist a stable internal identifier for one Cognito subject."""

    __tablename__ = "identities"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    external_subject: Mapped[str] = mapped_column(String(128), unique=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
