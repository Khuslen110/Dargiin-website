"""Хэрэглэгчийн эрхийг роль болон удирдах хүнээр тодорхойлох

Revision ID: 0003_simple_users
Revises: 0002_hierarchy
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_simple_users"
down_revision: str | None = "0002_hierarchy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role RENAME VALUE 'USER' TO 'LEADER'")
    op.drop_table("user_scopes")
    op.drop_column("users", "can_edit")
    op.drop_column("users", "can_import")
    op.drop_column("users", "can_export")
    op.drop_column("users", "can_view_sensitive")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("can_edit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("can_import", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("can_export", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column(
            "can_view_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.create_table(
        "user_scopes",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("root_person_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["root_person_id"], ["people.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id", "root_person_id"),
    )
    op.execute(
        """
        INSERT INTO user_scopes (user_id, root_person_id)
        SELECT id, leader_person_id FROM users WHERE leader_person_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )
    op.execute("UPDATE users SET can_edit = true, can_view_sensitive = true WHERE role = 'LEADER'")
    op.execute("ALTER TYPE user_role RENAME VALUE 'LEADER' TO 'USER'")
