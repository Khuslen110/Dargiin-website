"""Анхны бүтэц: хэрэглэгч, хүн, харьяалал, аудит, импорт

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = sa.Enum("ADMIN", "USER", name="user_role")
gender = sa.Enum("MALE", "FEMALE", "OTHER", name="gender")
group_type = sa.Enum("TUMT", "MYANGAT", "ZUUT", "ARAVT", name="group_type")
person_status = sa.Enum("ACTIVE", "DELETED", name="person_status")
notification_kind = sa.Enum("INFO", "SUCCESS", "WARNING", name="notification_kind")
import_status = sa.Enum(
    "PREVIEWED", "PROCESSING", "COMPLETED", "FAILED", name="import_status"
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="USER"),
        sa.Column("can_edit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_import", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_export", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "can_view_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "people",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("reg_number", sa.String(length=10), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("gender", gender, nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("district", sa.String(length=80), nullable=True),
        sa.Column("khoroo", sa.String(length=80), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("job", sa.String(length=120), nullable=True),
        sa.Column("group_type", group_type, nullable=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("created_by_id", sa.BigInteger(), nullable=False),
        sa.Column("status", person_status, nullable=False, server_default="ACTIVE"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["people.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["deleted_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reg_number", name="uq_people_reg_number"),
    )
    op.create_index("ix_people_status_created", "people", ["status", "created_at"])
    op.create_index("ix_people_parent", "people", ["parent_id"])
    op.create_index("ix_people_group_type", "people", ["group_type"])
    op.create_index("ix_people_district", "people", ["district"])
    op.create_index("ix_people_khoroo", "people", ["khoroo"])
    op.create_index("ix_people_created_by", "people", ["created_by_id"])
    # pg_trgm суулгагдаагүй орчинд ажиллахын тулд PostgreSQL-ийн built-in
    # full-text search (simple config) + prefix query ашиглана.
    op.create_index(
        "ix_people_last_name_fts",
        "people",
        [sa.text("to_tsvector('simple', last_name)")],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_people_first_name_fts",
        "people",
        [sa.text("to_tsvector('simple', first_name)")],
        postgresql_using="gin",
    )
    op.create_index("ix_people_last_name", "people", ["last_name"])
    op.create_index("ix_people_first_name", "people", ["first_name"])
    op.execute(
        "CREATE INDEX ix_people_district_lower ON people (lower(district) text_pattern_ops)"
    )
    op.execute(
        "CREATE INDEX ix_people_khoroo_lower ON people (lower(khoroo) text_pattern_ops)"
    )

    op.create_table(
        "person_closure",
        sa.Column("ancestor_id", sa.BigInteger(), nullable=False),
        sa.Column("descendant_id", sa.BigInteger(), nullable=False),
        sa.Column("depth", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("depth >= 0", name="ck_person_closure_depth"),
        sa.ForeignKeyConstraint(["ancestor_id"], ["people.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["descendant_id"], ["people.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("ancestor_id", "descendant_id"),
    )
    op.create_index("ix_person_closure_descendant", "person_closure", ["descendant_id"])

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

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token", sa.String(length=64), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index(
        "ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("actor_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=True),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_created", "audit_logs", ["created_at"])
    op.create_index("ix_audit_actor_created", "audit_logs", ["actor_id", "created_at"])
    op.create_index("ix_audit_entity", "audit_logs", ["entity_type", "entity_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.String(length=500), nullable=False),
        sa.Column("kind", notification_kind, nullable=False, server_default="INFO"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notifications_user_read",
        "notifications",
        ["user_id", "read_at", "created_at"],
    )

    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("status", import_status, nullable=False, server_default="PREVIEWED"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalid_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "errors",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_jobs_user_id", "import_jobs", ["user_id"])


def downgrade() -> None:
    op.drop_table("import_jobs")
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("user_sessions")
    op.drop_table("user_scopes")
    op.drop_table("person_closure")
    op.drop_table("people")
    op.drop_table("users")

    for enum in (import_status, notification_kind, person_status, group_type, gender, user_role):
        enum.drop(op.get_bind(), checkfirst=True)
