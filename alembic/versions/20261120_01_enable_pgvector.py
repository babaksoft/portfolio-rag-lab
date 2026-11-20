"""Enable the pgvector PostgreSQL extension.

Revision ID: 20261120_01
Revises: None
Created: 2026-11-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261120_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable vector storage and similarity operations."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Disable vector support while no project schema depends on it."""
    op.execute("DROP EXTENSION IF EXISTS vector")
