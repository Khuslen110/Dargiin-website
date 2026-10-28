from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.group_rules import group_type_error, is_valid_child, next_group_type
from app.core.security import password_policy_errors
from app.core.validation import (
    clean_text,
    normalize_phone,
    validate_phone,
    validate_reg_number,
    validate_username,
)
from app.importer.constants import (
    GENDER_LABELS,
    GROUP_TYPE_LABELS,
    MAX_TEXT_LENGTHS,
    REQUIRED_FIELDS,
)
from app.models.enums import GroupType, PersonStatus
from app.models.person import Person, PersonClosure
from app.models.user import User
from app.permissions import policy

MAX_ERRORS = 200
DATE_FORMATS = ("%Y-%m-%d", "%Y.%m.%d", "%d.%m.%Y")


@dataclass
class ValidRow:
    row_number: int
    data: dict[str, Any]
    parent_reg_number: str | None = None
    parent_id: int | None = None
    username: str | None = None
    password: str | None = None


@dataclass
class ChunkResult:
    valid: list[ValidRow] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    invalid: int = 0
    accounts_planned: int = 0


def _error(
    errors: list[dict[str, Any]], row: int, message: str, field_name: str | None = None
) -> None:
    if len(errors) < MAX_ERRORS:
        errors.append({"row": row, "message": message, "field": field_name})


def parse_birth_date(value: str) -> date | None:
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value.strip(), fmt).date()
            if parsed > date.today():
                raise ValueError
            if parsed.year < 1900:
                raise ValueError
            return parsed
        except ValueError:
            continue
    raise ValueError("Төрсөн огноо YYYY-MM-DD хэлбэрээр байх ёстой.")


def validate_chunk(
    db: Session,
    user: User,
    rows: list[tuple[int, dict[str, str]]],
    *,
    seen_regs: set[str],
    seen_usernames: set[str],
    earlier_valid_regs: set[str],
    default_parent: Person | None = None,
) -> ChunkResult:
    result = ChunkResult()
    candidates: list[tuple[int, dict[str, Any], str | None, str | None, str | None]] = []

    for row_number, raw in rows:
        row_errors: list[str] = []
        field_messages: dict[str, str] = {}
        data: dict[str, Any] = {}

        reg_raw = raw.get("reg_number", "")
        try:
            reg_number = validate_reg_number(reg_raw)
        except ValueError as exc:
            row_errors.append(str(exc))
            reg_number = ""

        if reg_number:
            if reg_number in seen_regs:
                row_errors.append("Регистрийн дугаар файл дотор давхцаж байна.")
            seen_regs.add(reg_number)
        data["reg_number"] = reg_number

        for field_name in ("last_name", "first_name"):
            cleaned = clean_text(raw.get(field_name))
            if not cleaned:
                row_errors.append("Овог, нэрийг заавал бөглөнө.")
            elif len(cleaned) > MAX_TEXT_LENGTHS[field_name]:
                row_errors.append(f"Талбарын урт {MAX_TEXT_LENGTHS[field_name]} тэмдэгтээс хэтэрсэн.")
            data[field_name] = cleaned or ""

        gender = GENDER_LABELS.get(raw.get("gender", "").strip().lower())
        if gender is None:
            row_errors.append("Хүйс нь Эрэгтэй, Эмэгтэй эсвэл Бусад байх ёстой.")
        data["gender"] = gender

        group_type = GROUP_TYPE_LABELS.get(raw.get("group_type", "").strip().lower())
        if group_type is None:
            row_errors.append("Бүлгийн төрөл нь Түмт, Мянгат, Зуут, Аравт эсвэл Гишүүн байх ёстой.")
        data["group_type"] = group_type

        try:
            data["birth_date"] = parse_birth_date(raw.get("birth_date", ""))
        except ValueError as exc:
            row_errors.append(str(exc))
            data["birth_date"] = None

        try:
            data["phone"] = validate_phone(raw.get("phone"))
        except ValueError as exc:
            row_errors.append(str(exc))
            data["phone"] = normalize_phone(raw.get("phone"))

        for field_name in ("district", "khoroo", "address", "job"):
            cleaned = clean_text(raw.get(field_name))
            if cleaned and len(cleaned) > MAX_TEXT_LENGTHS[field_name]:
                row_errors.append(f"Талбарын урт {MAX_TEXT_LENGTHS[field_name]} тэмдэгтээс хэтэрсэн.")
            data[field_name] = cleaned

        username: str | None = None
        username_raw = raw.get("username", "").strip()
        password = raw.get("password", "").strip() or None
        if username_raw:
            try:
                username = validate_username(username_raw)
            except ValueError as exc:
                row_errors.append(str(exc))
                field_messages[str(exc)] = "username"
        if password:
            for message in password_policy_errors(password):
                row_errors.append(message)
                field_messages[message] = "password"
        elif username_raw:
            message = "Хэрэглэгчийн нэр оруулсан бол нууц үг оруулна уу."
            row_errors.append(message)
            field_messages[message] = "password"
        if username:
            if username in seen_usernames:
                message = "Хэрэглэгчийн нэр файл дотор давхцаж байна."
                row_errors.append(message)
                field_messages[message] = "username"
            seen_usernames.add(username)

        parent_reg: str | None = None
        parent_raw = raw.get("parent_reg_number", "").strip()
        if parent_raw:
            try:
                parent_reg = validate_reg_number(parent_raw)
            except ValueError:
                row_errors.append("Харьяалагдах хүний регистрийн дугаар буруу форматтай.")
            if default_parent is not None and parent_reg != default_parent.reg_number:
                row_errors.append("Сонгосон хүнээс өөр харьяалал зааж болохгүй.")
        elif default_parent is not None:
            parent_reg = default_parent.reg_number
        if parent_reg is None and not policy.is_admin(user):
            row_errors.append("Энгийн хэрэглэгч харьяалагдах хүнгүй бүртгэл оруулах боломжгүй.")
        if default_parent is not None and group_type == GroupType.TUMT:
            row_errors.append(
                "Сонгосон хүний доор Түмт оруулах боломжгүй. "
                "Түмт оруулах бол харьяалагдах хүнгүйгээр импортлоно уу."
            )

        if row_errors:
            result.invalid += 1
            for message in row_errors:
                _error(result.errors, row_number, message, field_messages.get(message))
            continue
        candidates.append((row_number, data, parent_reg, username, password))

    # DB-д байгаа регистр/хэрэглэгчийн нэрийг нэг query-ээр шалгана.
    regs = [data["reg_number"] for _, data, _, _, _ in candidates if data.get("reg_number")]
    existing = set()
    if regs:
        existing = set(db.scalars(select(Person.reg_number).where(Person.reg_number.in_(regs))))
    usernames = [username for _, _, _, username, _ in candidates if username]
    existing_usernames = set()
    if usernames:
        existing_usernames = set(
            db.scalars(select(User.username).where(User.username.in_(usernames)))
        )

    candidate_regs = {data["reg_number"] for _, data, _, _, _ in candidates}
    candidate_groups = {
        data["reg_number"]: data["group_type"] for _, data, _, _, _ in candidates
    }
    parent_regs = {parent for _, _, parent, _, _ in candidates if parent}
    parents_by_reg: dict[str, Person] = {}
    if parent_regs:
        parents_by_reg = {
            person.reg_number: person
            for person in db.scalars(select(Person).where(Person.reg_number.in_(parent_regs)))
        }

    visible_parent_ids: set[int] = set()
    if not policy.is_admin(user) and parents_by_reg:
        roots = policy.scope_root_ids(user)
        parent_ids = [person.id for person in parents_by_reg.values()]
        if roots and parent_ids:
            visible_parent_ids = set(
                db.scalars(
                    select(PersonClosure.descendant_id).where(
                        PersonClosure.ancestor_id.in_(roots),
                        PersonClosure.descendant_id.in_(parent_ids),
                    )
                )
            )

    leader = None if policy.is_admin(user) else policy.leader_person(user)
    leader_expected = next_group_type(leader.group_type) if leader else None

    for row_number, data, parent_reg, username, password in candidates:
        row_errors: list[str] = []
        if data["reg_number"] in existing:
            row_errors.append("Энэ регистрийн дугаар өмнө нь бүртгэгдсэн байна.")
        if username and username in existing_usernames:
            message = "Энэ хэрэглэгчийн нэр өмнө нь бүртгэгдсэн байна."
            row_errors.append(message)
            field_messages[message] = "username"

        parent_id = None
        parent_group = None
        if parent_reg:
            parent = parents_by_reg.get(parent_reg)
            if parent is not None:
                if parent.status != PersonStatus.ACTIVE:
                    row_errors.append("Харьяалагдах хүн идэвхгүй (устгасан) байна.")
                elif not policy.is_admin(user) and parent.id not in visible_parent_ids:
                    row_errors.append("Харьяалагдах хүн таны харьяалалд байхгүй.")
                else:
                    parent_id = parent.id
                    parent_group = parent.group_type
            elif parent_reg not in candidate_regs and parent_reg not in earlier_valid_regs:
                row_errors.append("Харьяалагдах хүн олдсонгүй. Эхлээд түүнийг бүртгэнэ үү.")
            elif parent_reg in candidate_regs:
                # Файл доторх мөрүүдийг эхлээд бүгдийг нь оруулаад дараа нь
                # recursive CTE-ээр closure байгуулна.
                parent_id = None
                parent_group = candidate_groups.get(parent_reg)
            else:
                earlier = db.scalars(
                    select(Person).where(Person.reg_number == parent_reg)
                ).first()
                if earlier is not None:
                    parent_id = earlier.id
                    parent_group = earlier.group_type

        group_type = data["group_type"]
        if parent_reg is None:
            if policy.is_admin(user) and group_type.value != "TUMT":
                row_errors.append("Үндсэн бүртгэл зөвхөн Түмт төрөлтэй байна.")
        else:
            if not policy.is_admin(user):
                if leader is None or parent_reg != leader.reg_number:
                    row_errors.append("Та зөвхөн өөрийн шууд доор хүн импортлох боломжтой.")
                elif leader_expected is None or group_type != leader_expected:
                    row_errors.append(group_type_error(leader.group_type))
            if parent_group is not None and not is_valid_child(parent_group, group_type):
                row_errors.append(group_type_error(parent_group))

        if row_errors:
            result.invalid += 1
            for message in row_errors:
                _error(result.errors, row_number, message, field_messages.get(message))
            continue

        result.valid.append(
            ValidRow(
                row_number=row_number,
                data=data,
                parent_reg_number=parent_reg,
                parent_id=parent_id,
                username=username,
                password=password,
            )
        )
        if password:
            result.accounts_planned += 1

    # Файл доторх харьяалал: эцэг мөр нь өөрөө алдаатай бол хүүхэд мөрийг ч
    # хүчингүй болгоно. (Preview-д таамагласан «valid» тоо буруу гарахаас сэргийлнэ.)
    while True:
        valid_regs = {row.data["reg_number"] for row in result.valid}
        removed = False
        for row in list(result.valid):
            parent_reg = row.parent_reg_number
            if (
                parent_reg
                and parent_reg not in valid_regs
                and parent_reg not in parents_by_reg
                and parent_reg not in earlier_valid_regs
            ):
                result.valid.remove(row)
                result.invalid += 1
                if row.password:
                    result.accounts_planned -= 1
                _error(
                    result.errors,
                    row.row_number,
                    "Харьяалагдах хүний мөр мөн алдаатай тул оруулах боломжгүй.",
                    "parent_reg_number",
                )
                removed = True
        if not removed:
            break

    return result


def normalize_header(header: list[str]) -> tuple[dict[int, str], list[str]]:
    from app.importer.constants import HEADER_ALIASES

    mapping: dict[int, str] = {}
    missing: list[str] = []
    seen: set[str] = set()
    for index, raw in enumerate(header):
        key = HEADER_ALIASES.get(raw.strip().lower())
        if key is None:
            continue
        if key in seen:
            missing.append(f"Давхардсан багана: {raw}")
            continue
        seen.add(key)
        mapping[index] = key
    for required in REQUIRED_FIELDS:
        if required not in seen:
            from app.importer.constants import FIELD_LABELS

            missing.append(f"Заавал багана дутуу: {FIELD_LABELS[required]}")
    return mapping, missing


def row_from_cells(mapping: dict[int, str], cells: list[str]) -> dict[str, str]:
    return {
        field_name: (cells[index] if index < len(cells) else "")
        for index, field_name in mapping.items()
    }


def is_empty_row(cells: list[str]) -> bool:
    return not any(cell.strip() for cell in cells)


def sanitize_formula(value: str) -> str:
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value

