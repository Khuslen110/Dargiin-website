import csv
import io
from datetime import UTC, datetime

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit_actions import AuditAction
from app.core.config import settings
from app.core.errors import forbidden
from app.core.time import age_from_birth_date
from app.importer.constants import GENDER_EXPORT_LABELS, GROUP_TYPE_EXPORT_LABELS
from app.importer.validation import sanitize_formula
from app.models.enums import PersonStatus
from app.models.person import Person
from app.models.user import User
from app.permissions import policy
from app.repositories import people as people_repo
from app.services import audit as audit_service
from app.services import people as people_service

EXPORT_HEADERS = [
    "Регистрийн дугаар",
    "Овог",
    "Нэр",
    "Хүйс",
    "Төрсөн огноо",
    "Нас",
    "Утас",
    "Дүүрэг",
    "Хороо",
    "Хаяг",
    "Ажил",
    "Бүлгийн төрөл",
    "Харьяалагдах хүний регистр",
    "Бүртгэсэн огноо",
]


def export_people(
    db: Session,
    user: User,
    *,
    fmt: str,
    filters: dict,
    ip: str | None = None,
) -> tuple[bytes, str, str, bool, int]:
    if not policy.can_export(user):
        raise forbidden("Экспорт хийх эрх танд байхгүй.")

    limit = settings.export_max_rows
    people, total = people_service.search_people(
        db,
        user,
        page=1,
        page_size=limit,
        status=PersonStatus.ACTIVE,
        sort="created_at",
        order="asc",
        **filters,
    )
    ids = [item.id for item in people]
    full: dict[int, Person] = {}
    if ids:
        full = {
            person.id: person
            for person in db.scalars(select(Person).where(Person.id.in_(ids)))
        }
    parent_ids = {item.parent_id for item in people if item.parent_id}
    parents = people_repo.persons_by_ids(db, list(parent_ids))
    sensitive = policy.can_view_sensitive(user)

    rows: list[list[str]] = []
    for item in people:
        person = full.get(item.id)
        parent = parents.get(item.parent_id) if item.parent_id else None
        phone = person.phone if (sensitive and person) else item.phone
        rows.append(
            [
                item.reg_number,
                item.last_name,
                item.first_name,
                GENDER_EXPORT_LABELS[item.gender],
                item.birth_date.isoformat() if item.birth_date else "",
                str(age_from_birth_date(item.birth_date) or ""),
                phone or "",
                item.district or "",
                item.khoroo or "",
                (person.address if person else "") if sensitive else "",
                (person.job or "") if person else "",
                GROUP_TYPE_EXPORT_LABELS[item.group_type],
                parent.reg_number if parent else "",
                item.created_at.astimezone(UTC).date().isoformat(),
            ]
        )

    truncated = total > limit
    audit_service.log(
        db,
        actor=user,
        action=AuditAction.EXPORT,
        entity_type="person",
        metadata={"format": fmt, "rows": len(rows), "truncated": truncated},
        ip=ip,
    )
    db.commit()

    timestamp = datetime.now(UTC).strftime("%Y%m%d")
    if fmt == "xlsx":
        content = _write_xlsx(rows)
        filename = f"people-registry-{timestamp}.xlsx"
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content = _write_csv(rows)
        filename = f"people-registry-{timestamp}.csv"
        content_type = "text/csv; charset=utf-8"
    return content, filename, content_type, truncated, len(rows)


def _safe(value: str) -> str:
    return sanitize_formula(str(value))


def _write_csv(rows: list[list[str]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_HEADERS)
    for row in rows:
        writer.writerow([_safe(value) for value in row])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def _write_xlsx(rows: list[list[str]]) -> bytes:
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("Бүртгэл")
    sheet.append(EXPORT_HEADERS)
    for row in rows:
        sheet.append([_safe(value) for value in row])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
