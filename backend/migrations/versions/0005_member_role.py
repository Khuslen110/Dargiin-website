"""Гишүүн хэрэглэгчийн эрх нэмэх

Revision ID: 0005_member_role
Revises: 0004_import_parent
Create Date: 2026-10-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_member_role"
down_revision: str | None = "0004_import_parent"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'MEMBER'")


def downgrade() -> None:
    pass
