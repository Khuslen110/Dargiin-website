"""Импортоор үүссэн хэрэглэгчийн тоог хадгалах

Revision ID: 0006_import_accounts
Revises: 0005_member_role
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_import_accounts"
down_revision: str | None = "0005_member_role"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "import_jobs",
        sa.Column("accounts_created", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("import_jobs", "accounts_created")
