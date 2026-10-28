from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    func,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Gender, GroupType, PersonStatus


def _enum(enum_cls, name: str) -> SAEnum:
    return SAEnum(enum_cls, name=name, values_callable=lambda items: [i.value for i in items])


class Person(Base):
    __tablename__ = "people"
    __table_args__ = (
        Index("ix_people_status_created", "status", "created_at"),
        Index("ix_people_parent", "parent_id"),
        Index("ix_people_group_type", "group_type"),
        Index("ix_people_district", "district"),
        Index("ix_people_khoroo", "khoroo"),
        Index("ix_people_created_by", "created_by_id"),
        Index("ix_people_last_name", "last_name"),
        Index("ix_people_first_name", "first_name"),
        Index(
            "ix_people_last_name_fts",
            text("to_tsvector('simple', last_name)"),
            postgresql_using="gin",
        ),
        Index(
            "ix_people_first_name_fts",
            text("to_tsvector('simple', first_name)"),
            postgresql_using="gin",
        ),
        Index(
            "ix_people_address_fts",
            text("to_tsvector('simple', coalesce(address, ''))"),
            postgresql_using="gin",
        ),
        Index(
            "ix_people_job_fts",
            text("to_tsvector('simple', coalesce(job, ''))"),
            postgresql_using="gin",
        ),
        Index("ix_people_birth_date", "birth_date"),
        Index(
            "ix_people_district_lower",
            text("lower(district)"),
            postgresql_ops={"lower": "text_pattern_ops"},
        ),
        Index(
            "ix_people_khoroo_lower",
            text("lower(khoroo)"),
            postgresql_ops={"lower": "text_pattern_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reg_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    gender: Mapped[Gender] = mapped_column(_enum(Gender, "gender"), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(20))
    district: Mapped[str | None] = mapped_column(String(80))
    khoroo: Mapped[str | None] = mapped_column(String(80))
    address: Mapped[str | None] = mapped_column(String(255))
    job: Mapped[str | None] = mapped_column(String(120))
    group_type: Mapped[GroupType] = mapped_column(_enum(GroupType, "group_type"), nullable=False)

    parent_id: Mapped[int | None] = mapped_column(ForeignKey("people.id", ondelete="RESTRICT"))
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    status: Mapped[PersonStatus] = mapped_column(
        _enum(PersonStatus, "person_status"), nullable=False, default=PersonStatus.ACTIVE
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    parent: Mapped["Person | None"] = relationship(
        remote_side=[id], back_populates="children", foreign_keys=[parent_id]
    )
    children: Mapped[list["Person"]] = relationship(
        back_populates="parent", foreign_keys=[parent_id]
    )
    creator: Mapped["User"] = relationship(foreign_keys=[created_by_id])  # noqa: F821
    deleted_by: Mapped["User | None"] = relationship(foreign_keys=[deleted_by_id])  # noqa: F821


class PersonClosure(Base):
    """Харьяаллын subtree-г хурдан шалгах closure table."""

    __tablename__ = "person_closure"
    __table_args__ = (
        CheckConstraint("depth >= 0", name="ck_person_closure_depth"),
        Index("ix_person_closure_descendant", "descendant_id"),
    )

    ancestor_id: Mapped[int] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), primary_key=True
    )
    descendant_id: Mapped[int] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), primary_key=True
    )
    depth: Mapped[int] = mapped_column(SmallInteger, nullable=False)


__all__ = ["Person", "PersonClosure"]
