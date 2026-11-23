"""Shared SQLAlchemy mapped-model registry."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class contributing metadata for project-owned tables."""
