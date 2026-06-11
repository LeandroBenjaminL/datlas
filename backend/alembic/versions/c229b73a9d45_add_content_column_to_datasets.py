"""add content column to datasets

Revision ID: c229b73a9d45
Revises: aabec5d9ad75
Create Date: 2026-06-11 13:34:32.702719

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c229b73a9d45"
down_revision: str | Sequence[str] | None = "aabec5d9ad75"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add content BYTEA column to datasets table."""
    op.add_column("datasets", sa.Column("content", sa.LargeBinary, nullable=True))


def downgrade() -> None:
    """Remove content column from datasets table."""
    op.drop_column("datasets", "content")
