"""Бүлгийн шатлал, удирдагч хэрэглэгч, хайлтын индекс

Revision ID: 0002_hierarchy
Revises: 0001_initial
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_hierarchy"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE group_type ADD VALUE IF NOT EXISTS 'MEMBER'")

    op.add_column("users", sa.Column("leader_person_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_users_leader_person",
        "users",
        "people",
        ["leader_person_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ux_users_leader_person_id", "users", ["leader_person_id"], unique=True
    )

    op.create_index("ix_people_birth_date", "people", ["birth_date"])
    op.execute(
        "CREATE INDEX ix_people_reg_number_prefix ON people (reg_number text_pattern_ops)"
    )
    op.execute(
        "CREATE INDEX ix_people_address_fts ON people "
        "USING gin (to_tsvector('simple', coalesce(address, '')))"
    )
    op.execute(
        "CREATE INDEX ix_people_job_fts ON people "
        "USING gin (to_tsvector('simple', coalesce(job, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_people_job_fts")
    op.execute("DROP INDEX IF EXISTS ix_people_address_fts")
    op.execute("DROP INDEX IF EXISTS ix_people_reg_number_prefix")
    op.drop_index("ix_people_birth_date", table_name="people")

    op.drop_index("ux_users_leader_person_id", table_name="users")
    op.drop_constraint("fk_users_leader_person", "users", type_="foreignkey")
    op.drop_column("users", "leader_person_id")

    # PostgreSQL нь enum-ээс утга устгахыг шууд дэмждэггүй тул MEMBER утга
    # ашиглагдаагүй үед type-ийг дахин үүсгэнэ.
    bind = op.get_bind()
    used = bind.execute(
        sa.text("SELECT count(*) FROM people WHERE group_type = 'MEMBER'")
    ).scalar_one()
    if used:
        raise RuntimeError("MEMBER бүртгэл байгаа тул downgrade хийх боломжгүй.")
    op.execute("ALTER TYPE group_type RENAME TO group_type_old")
    op.execute("CREATE TYPE group_type AS ENUM ('TUMT', 'MYANGAT', 'ZUUT', 'ARAVT')")
    op.execute(
        "ALTER TABLE people ALTER COLUMN group_type TYPE group_type "
        "USING group_type::text::group_type"
    )
    op.execute("DROP TYPE group_type_old")
