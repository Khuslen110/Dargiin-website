import csv
import io
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import bindparam, insert, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit_actions import AuditAction
from app.core.config import settings
from app.core.errors import AppError, bad_request, conflict, forbidden, not_found
from app.core.group_rules import can_be_leader
from app.core.security import hash_password
from app.importer.constants import FIELD_LABELS
from app.importer.reader import read_header
from app.importer.storage import delete_file, save_upload
from app.importer.validation import (
    ValidRow,
    is_empty_row,
    normalize_header,
    row_from_cells,
    sanitize_formula,
    validate_chunk,
)
from app.models.enums import GroupType, ImportStatus, NotificationKind, PersonStatus, Role
from app.models.import_job import ImportJob
from app.models.person import Person, PersonClosure
from app.models.user import User
from app.permissions import policy
from app.repositories import imports as imports_repo
from app.repositories import notifications as notifications_repo
from app.schemas.import_job import ImportErrorItem, ImportJobOut, ImportPreview
from app.services import audit as audit_service

CHUNK_SIZE = 500
MAX_ERRORS_STORED = 100


class MissingParentError(Exception):
    pass


@dataclass
class ValidationSummary:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    imported: int = 0
    accounts_planned: int = 0
    accounts_created: int = 0
    errors: list[dict] = field(default_factory=list)


def _store_errors(errors: list[dict]) -> list[dict]:
    return errors[:MAX_ERRORS_STORED]


def preview_job(
    db: Session, user: User, job: ImportJob, *, ip: str | None = None
) -> ImportPreview:
    if not policy.can_import(user):
        raise forbidden("Импорт хийх эрх танд байхгүй.")
    try:
        summary = _validate_file(
            db, user, Path(job.file_path), insert=False, default_parent_id=job.parent_id
        )
    except AppError:
        job.status = ImportStatus.FAILED
        job.errors = [{"row": 0, "message": "Файлыг шалгаж чадсангүй.", "field": None}]
        job.completed_at = datetime.now(UTC)
        db.commit()
        delete_file(job.file_path)
        raise

    job.total_rows = summary.total
    job.valid_rows = summary.valid
    job.invalid_rows = summary.invalid
    job.errors = _store_errors(summary.errors)
    job.status = ImportStatus.PREVIEWED
    audit_service.log(
        db,
        actor=user,
        action=AuditAction.IMPORT_START,
        entity_type="import",
        metadata={"job_id": str(job.id), "rows": summary.total},
        ip=ip,
    )
    db.commit()
    return ImportPreview(
        job_id=str(job.id),
        filename=job.filename,
        total_rows=summary.total,
        valid_rows=summary.valid,
        invalid_rows=summary.invalid,
        errors=[ImportErrorItem(**error) for error in job.errors],
        can_confirm=summary.valid > 0,
        accounts_planned=summary.accounts_planned,
    )


def _validate_file(
    db: Session,
    user: User,
    path: Path,
    *,
    insert: bool,
    default_parent_id: int | None = None,
) -> ValidationSummary:
    if not path.exists():
        raise bad_request("Импортын файл олдсонгүй. Дахин оруулна уу.")
    header, rows = read_header(path)
    mapping, header_errors = normalize_header(header)
    if header_errors:
        raise bad_request("Файлын толгой мөр буруу: " + "; ".join(header_errors))

    default_parent = _load_default_parent(db, default_parent_id)
    summary = ValidationSummary()
    seen_regs: set[str] = set()
    seen_usernames: set[str] = set()
    earlier_valid_regs: set[str] = set()
    chunk: list[tuple[int, dict[str, str]]] = []

    def process_chunk() -> None:
        if not chunk:
            return
        result = validate_chunk(
            db,
            user,
            chunk,
            seen_regs=seen_regs,
            seen_usernames=seen_usernames,
            earlier_valid_regs=earlier_valid_regs,
            default_parent=default_parent,
        )
        summary.valid += len(result.valid)
        summary.invalid += result.invalid
        summary.accounts_planned += result.accounts_planned
        summary.errors.extend(result.errors)
        if insert and result.valid:
            imported, accounts, insert_errors = _insert_rows(db, user, result.valid)
            summary.imported += imported
            summary.accounts_created += accounts
            summary.invalid += len(insert_errors)
            summary.errors.extend(insert_errors)
        if insert:
            inserted_regs = [row.data["reg_number"] for row in result.valid]
            if inserted_regs:
                actual = set(
                    db.scalars(
                        select(Person.reg_number).where(
                            Person.reg_number.in_(inserted_regs)
                        )
                    )
                )
                earlier_valid_regs.update(actual)
        else:
            earlier_valid_regs.update(row.data["reg_number"] for row in result.valid)
        chunk.clear()

    for row_number, cells in rows:
        if is_empty_row(cells):
            continue
        summary.total += 1
        if summary.total > settings.import_max_rows:
            raise bad_request(
                f"Нэг импортод {settings.import_max_rows:_} мөрөөс илүү оруулах боломжгүй."
            )
        chunk.append((row_number, row_from_cells(mapping, cells)))
        if len(chunk) >= CHUNK_SIZE:
            process_chunk()
    process_chunk()
    return summary


def _load_default_parent(db: Session, parent_id: int | None) -> Person | None:
    if parent_id is None:
        return None
    parent = db.get(Person, parent_id)
    if parent is None or parent.status != PersonStatus.ACTIVE:
        raise bad_request("Харьяалагдах хүн олдсонгүй эсвэл идэвхгүй байна.")
    if not can_be_leader(parent.group_type):
        raise bad_request("Гишүүн төрөлтэй хүний доор бүртгэл оруулах боломжгүй.")
    return parent


def _person_from_row(row: ValidRow, user: User) -> Person:
    data = row.data
    return Person(
        reg_number=data["reg_number"],
        last_name=data["last_name"],
        first_name=data["first_name"],
        gender=data["gender"],
        birth_date=data["birth_date"],
        phone=data["phone"],
        district=data["district"],
        khoroo=data["khoroo"],
        address=data["address"],
        job=data["job"],
        group_type=data["group_type"],
        parent_id=row.parent_id,
        created_by_id=user.id,
        status=PersonStatus.ACTIVE,
    )


def _resolve_parents(db: Session, rows: list[ValidRow], people: list[Person]) -> None:
    reg_map = {person.reg_number: person.id for person in people}
    for row, person in zip(rows, people, strict=True):
        if person.parent_id is not None or not row.parent_reg_number:
            continue
        parent_id = reg_map.get(row.parent_reg_number)
        if parent_id is None:
            parent_id = db.scalars(
                select(Person.id).where(Person.reg_number == row.parent_reg_number)
            ).first()
        if parent_id is None:
            raise MissingParentError(row.parent_reg_number)
        person.parent_id = parent_id


def _insert_batch(db: Session, user: User, rows: list[ValidRow]) -> int:
    people = [_person_from_row(row, user) for row in rows]
    db.add_all(people)
    db.flush()
    _resolve_parents(db, rows, people)
    db.flush()

    ids = [person.id for person in people]
    db.execute(
        insert(PersonClosure),
        [
            {"ancestor_id": person_id, "descendant_id": person_id, "depth": 0}
            for person_id in ids
        ],
    )
    closure_sql = text(
        """
        WITH RECURSIVE chain AS (
            SELECT p.id AS descendant_id, p.parent_id AS ancestor_id, 1 AS depth
            FROM people p
            WHERE p.id IN :ids AND p.parent_id IS NOT NULL
            UNION ALL
            SELECT c.descendant_id, p.parent_id, c.depth + 1
            FROM chain c
            JOIN people p ON p.id = c.ancestor_id
            WHERE p.parent_id IS NOT NULL
        )
        INSERT INTO person_closure (ancestor_id, descendant_id, depth)
        SELECT ancestor_id, descendant_id, depth FROM chain
        ON CONFLICT (ancestor_id, descendant_id) DO NOTHING
        """
    ).bindparams(bindparam("ids", expanding=True))
    db.execute(closure_sql, {"ids": ids})
    return _create_accounts(db, user, rows, people)


def _create_accounts(
    db: Session, actor: User, rows: list[ValidRow], people: list[Person]
) -> int:
    created = 0
    for row, person in zip(rows, people, strict=True):
        if not row.password:
            continue
        username = row.username or _auto_username(db, person.id)
        role = Role.MEMBER if person.group_type == GroupType.MEMBER else Role.LEADER
        account = User(
            username=username,
            full_name=f"{person.last_name} {person.first_name}"[:120],
            password_hash=hash_password(row.password),
            role=role,
            leader_person_id=person.id,
            is_active=True,
        )
        db.add(account)
        db.flush()
        audit_service.log(
            db,
            actor=actor,
            action=AuditAction.USER_CREATE,
            entity_type="user",
            entity_id=account.id,
            metadata={
                "role": role.value,
                "leader_person_id": person.id,
                "source": "import",
            },
        )
        notifications_repo.create(
            db,
            user_id=account.id,
            title="Тавтай морилно уу",
            body="Танд энэ системд нэвтрэх эрх үүслээ. Нууц үгээ Тохиргоо хэсгээс солих боломжтой.",
            kind=NotificationKind.INFO,
        )
        created += 1
    return created


def _auto_username(db: Session, person_id: int) -> str:
    base = f"user{person_id}"
    candidate = base
    suffix = 2
    while db.scalars(select(User.id).where(User.username == candidate)).first() is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _insert_rows(
    db: Session, user: User, rows: list[ValidRow]
) -> tuple[int, int, list[dict]]:
    try:
        with db.begin_nested():
            accounts = _insert_batch(db, user, rows)
        db.commit()
        return len(rows), accounts, []
    except (IntegrityError, MissingParentError):
        # Зэрэгцээ өөрчлөлт/нэг мөрийн алдаа гарвал мөр тус бүрээр дахин оролдоно.
        return _insert_individually(db, user, rows)


def _insert_individually(
    db: Session, user: User, rows: list[ValidRow]
) -> tuple[int, int, list[dict]]:
    imported = 0
    accounts = 0
    errors: list[dict] = []
    chunk_regs = {row.data["reg_number"] for row in rows}
    resolved: set[str] = set()
    pending = list(rows)

    while pending:
        progress = False
        next_round: list[ValidRow] = []
        for row in pending:
            parent_reg = row.parent_reg_number
            if (
                parent_reg
                and parent_reg in chunk_regs
                and parent_reg not in resolved
            ):
                next_round.append(row)
                continue
            try:
                with db.begin_nested():
                    row_accounts = _insert_batch(db, user, [row])
                db.commit()
                imported += 1
                accounts += row_accounts
                resolved.add(row.data["reg_number"])
                progress = True
            except (IntegrityError, MissingParentError):
                errors.append(
                    {
                        "row": row.row_number,
                        "message": "Мөрийг оруулах боломжгүй: өгөгдлийн зөрчил эсвэл харьяалал олдсонгүй.",
                        "field": None,
                    }
                )
        if not progress:
            for row in next_round:
                errors.append(
                    {
                        "row": row.row_number,
                        "message": "Харьяалагдах хүний мөр мөн алдаатай тул оруулж чадсангүй.",
                        "field": "parent_reg_number",
                    }
                )
            break
        pending = next_round
    return imported, accounts, errors


def confirm_job(
    db: Session, user: User, job_id: uuid.UUID, *, ip: str | None = None
) -> ImportJobOut:
    if not policy.can_import(user):
        raise forbidden("Импорт хийх эрх танд байхгүй.")
    job = imports_repo.get_job_for_update(db, job_id)
    if job is None:
        raise not_found("Импортын ажил олдсонгүй.")
    if job.user_id != user.id and not policy.is_admin(user):
        raise not_found("Импортын ажил олдсонгүй.")
    if job.status != ImportStatus.PREVIEWED:
        raise conflict("Энэ импортыг баталгаажуулах боломжгүй төлөвт байна.")

    job.status = ImportStatus.PROCESSING
    db.commit()

    try:
        summary = _validate_file(
            db, user, Path(job.file_path), insert=True, default_parent_id=job.parent_id
        )
        job = imports_repo.get_job(db, job_id)
        assert job is not None
        job.total_rows = summary.total
        job.valid_rows = summary.valid
        job.invalid_rows = summary.invalid
        job.imported_rows = summary.imported
        job.accounts_created = summary.accounts_created
        job.errors = _store_errors(summary.errors)
        job.status = ImportStatus.COMPLETED
        job.completed_at = datetime.now(UTC)
        audit_service.log(
            db,
            actor=user,
            action=AuditAction.IMPORT_COMPLETE,
            entity_type="import",
            metadata={
                "job_id": str(job.id),
                "imported": summary.imported,
                "accounts_created": summary.accounts_created,
                "invalid": summary.invalid,
            },
            ip=ip,
        )
        notifications_repo.create(
            db,
            user_id=user.id,
            title="Импорт дууслаа",
            body=(
                f"{summary.imported} бүртгэл, {summary.accounts_created} хэрэглэгч нэмэгдлээ. "
                f"{summary.invalid} мөр алдаатай байсан."
            ),
            kind=(
                NotificationKind.SUCCESS
                if summary.invalid == 0
                else NotificationKind.WARNING
            ),
        )
        db.commit()
    except AppError as exc:
        job = imports_repo.get_job(db, job_id)
        assert job is not None
        job.status = ImportStatus.FAILED
        job.completed_at = datetime.now(UTC)
        job.errors = [{"row": 0, "message": exc.detail, "field": None}]
        db.commit()
        delete_file(job.file_path)
        raise
    except Exception as exc:  # noqa: BLE001 - job-ийн төлөвийг заавал хадгална
        db.rollback()
        job = imports_repo.get_job(db, job_id)
        assert job is not None
        job.status = ImportStatus.FAILED
        job.completed_at = datetime.now(UTC)
        job.errors = [
            {"row": 0, "message": "Импортын явцад системийн алдаа гарлаа.", "field": None}
        ]
        db.commit()
        delete_file(job.file_path)
        raise AppError(500, "Импортын явцад алдаа гарлаа. Файлаа шалгана уу.") from exc

    delete_file(job.file_path)
    return job_out(job)


def job_out(job: ImportJob) -> ImportJobOut:
    return ImportJobOut(
        id=str(job.id),
        filename=job.filename,
        status=job.status,
        total_rows=job.total_rows,
        valid_rows=job.valid_rows,
        invalid_rows=job.invalid_rows,
        imported_rows=job.imported_rows,
        accounts_created=job.accounts_created,
        errors=job.errors or [],
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


def error_report_csv(job: ImportJob) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Мөрийн дугаар", "Алдаа", "Талбар"])
    for error in job.errors or []:
        writer.writerow(
            [
                error.get("row", ""),
                sanitize_formula(str(error.get("message", ""))),
                sanitize_formula(str(error.get("field") or "")),
            ]
        )
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def template_csv() -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [label for key, label in FIELD_LABELS.items() if key != "parent_reg_number"]
    )
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def create_uploaded_job(
    db: Session,
    user: User,
    *,
    job_id: uuid.UUID,
    path: Path,
    filename: str,
    parent_id: int | None = None,
) -> ImportJob:
    job = imports_repo.create_job(
        db,
        job_id=job_id,
        user_id=user.id,
        filename=filename,
        file_path=str(path),
        parent_id=parent_id,
    )
    return job


__all__ = [
    "create_uploaded_job",
    "preview_job",
    "confirm_job",
    "job_out",
    "error_report_csv",
    "template_csv",
    "save_upload",
]
