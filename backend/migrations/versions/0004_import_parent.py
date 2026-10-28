"""Импортын харьяалах хүнийг хадгалах

Revision ID: 0004_import_parent
Revises: 0003_simple_users
Create Date: 2026-10-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_import_parent"
down_revision: str | None = "0003_simple_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "import_jobs",
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_import_jobs_parent_id_people",
        "import_jobs",
        "people",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_import_jobs_parent_id_people", "import_jobs", type_="foreignkey"
    )
    op.drop_column("import_jobs", "parent_id")
