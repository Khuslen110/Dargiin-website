import re
from datetime import date

from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.orm import Session, aliased, selectinload

from app.models.enums import GroupType, PersonStatus
from app.models.person import Person, PersonClosure
from app.models.user import User
from app.permissions.policy import (
    is_admin,
    scope_condition_for,
    scope_root_ids,
    visibility_condition,
    visibility_condition_for,
)

SORT_COLUMNS = {
    "created_at": Person.created_at,
    "updated_at": Person.updated_at,
    "last_name": Person.last_name,
    "first_name": Person.first_name,
    "reg_number": Person.reg_number,
    "district": Person.district,
    "khoroo": Person.khoroo,
    "group_type": Person.group_type,
    "birth_date": Person.birth_date,
}


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


_WORD_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁёӨөҮү]+")


def _fts_prefix_query(value: str) -> str:
    words = _WORD_RE.findall(value)
    return " & ".join(f"{word}:*" for word in words)


def _fts_condition(column, value: str):
    query = _fts_prefix_query(value)
    if not query:
        return None
    return func.to_tsvector("simple", column).op("@@")(func.to_tsquery("simple", query))


def _fts_condition_coalesced(column, value: str):
    query = _fts_prefix_query(value)
    if not query:
        return None
    return func.to_tsvector("simple", func.coalesce(column, "")).op("@@")(
        func.to_tsquery("simple", query)
    )


def get_visible(
    db: Session, user: User, person_id: int, *, include_deleted: bool = True
) -> Person | None:
    stmt = (
        select(Person)
        .options(selectinload(Person.creator))
        .where(Person.id == person_id, visibility_condition(user))
    )
    if not include_deleted:
        stmt = stmt.where(Person.status == PersonStatus.ACTIVE)
    return db.scalars(stmt).first()


def get_visible_for_update(db: Session, user: User, person_id: int) -> Person | None:
    stmt = (
        select(Person)
        .where(Person.id == person_id, visibility_condition(user))
        .with_for_update()
    )
    return db.scalars(stmt).first()


def get_any(db: Session, person_id: int) -> Person | None:
    return db.get(Person, person_id)


def register_number_taken(db: Session, reg_number: str) -> bool:
    return db.scalars(select(Person.id).where(Person.reg_number == reg_number)).first() is not None


def search_people(
    db: Session,
    user: User,
    *,
    page: int,
    page_size: int,
    reg_number: str | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
    phone: str | None = None,
    district: str | None = None,
    khoroo: str | None = None,
    address: str | None = None,
    job: str | None = None,
    gender=None,
    birth_date_from: date | None = None,
    birth_date_to: date | None = None,
    group_type=None,
    under_person_id: int | None = None,
    direct_only: bool = False,
    created_by_id: int | None = None,
    status: PersonStatus = PersonStatus.ACTIVE,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[Person], int]:
    conditions = [visibility_condition(user), Person.status == status]
    if reg_number:
        normalized = re.sub(r"[\s\-_]", "", reg_number).upper()
        if re.fullmatch(r"[А-ЯЁӨҮ]{2}\d{8}", normalized):
            conditions.append(Person.reg_number == normalized)
        elif normalized:
            conditions.append(
                Person.reg_number.like(f"{_escape_like(normalized)}%", escape="\\")
            )
    if last_name and (condition := _fts_condition(Person.last_name, last_name)) is not None:
        conditions.append(condition)
    if first_name and (condition := _fts_condition(Person.first_name, first_name)) is not None:
        conditions.append(condition)
    if phone:
        normalized_phone = re.sub(r"[^0-9+]", "", phone)
        if normalized_phone:
            conditions.append(
                Person.phone.ilike(f"%{_escape_like(normalized_phone)}%", escape="\\")
            )
    if district and district.strip():
        conditions.append(
            func.lower(Person.district).like(
                f"{_escape_like(district.strip().lower())}%", escape="\\"
            )
        )
    if khoroo and khoroo.strip():
        conditions.append(
            func.lower(Person.khoroo).like(
                f"{_escape_like(khoroo.strip().lower())}%", escape="\\"
            )
        )
    if address and (condition := _fts_condition_coalesced(Person.address, address)) is not None:
        conditions.append(condition)
    if job and (condition := _fts_condition_coalesced(Person.job, job)) is not None:
        conditions.append(condition)
    if gender is not None:
        conditions.append(Person.gender == gender)
    if birth_date_from is not None:
        conditions.append(Person.birth_date >= birth_date_from)
    if birth_date_to is not None:
        conditions.append(Person.birth_date <= birth_date_to)
    if group_type is not None:
        conditions.append(Person.group_type == group_type)
    if created_by_id is not None:
        conditions.append(Person.created_by_id == created_by_id)
    if under_person_id is not None:
        if direct_only:
            conditions.append(Person.parent_id == under_person_id)
        else:
            conditions.append(
                Person.id.in_(
                    select(PersonClosure.descendant_id).where(
                        PersonClosure.ancestor_id == under_person_id,
                        PersonClosure.depth > 0,
                    )
                )
            )

    count_stmt = select(func.count()).select_from(Person)
    base: Select = select(Person)
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
        base = base.where(condition)
    total = db.scalar(count_stmt) or 0

    sort_column = SORT_COLUMNS.get(sort, Person.created_at)
    ordering = sort_column.asc() if order == "asc" else sort_column.desc()
    stmt = (
        base.order_by(ordering, Person.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(stmt)), total


def child_group_types(db: Session, parent_id: int) -> list:
    return list(
        db.scalars(
            select(Person.group_type).where(
                Person.parent_id == parent_id, Person.status == PersonStatus.ACTIVE
            )
        )
    )


def recent_people(db: Session, user: User, limit: int = 5) -> list[Person]:
    stmt = (
        select(Person)
        .where(visibility_condition(user), Person.status == PersonStatus.ACTIVE)
        .order_by(Person.created_at.desc(), Person.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def direct_members(
    db: Session, user: User, parent_id: int, *, page: int, page_size: int
) -> tuple[list[Person], int]:
    conditions = [
        Person.parent_id == parent_id,
        Person.status == PersonStatus.ACTIVE,
        visibility_condition(user),
    ]
    count_stmt = select(func.count()).select_from(Person)
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
    total = db.scalar(count_stmt) or 0
    stmt = (
        select(Person)
        .where(*conditions)
        .order_by(Person.last_name.asc(), Person.first_name.asc(), Person.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(stmt)), total


def count_direct_members(db: Session, parent_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Person)
            .where(Person.parent_id == parent_id, Person.status == PersonStatus.ACTIVE)
        )
        or 0
    )


def path_to_person(db: Session, user: User, person_id: int) -> list[Person]:
    ancestor = aliased(Person)
    stmt = (
        select(ancestor)
        .join(PersonClosure, PersonClosure.ancestor_id == ancestor.id)
        .where(
            PersonClosure.descendant_id == person_id,
            PersonClosure.depth > 0,
            visibility_condition_for(user, ancestor.id),
        )
        .order_by(PersonClosure.depth.desc())
    )
    return list(db.scalars(stmt))


def parent_candidates(
    db: Session,
    user: User,
    *,
    search: str | None,
    limit: int = 20,
    group_type=None,
    leader_only: bool = False,
    member_only: bool = False,
    full_only: bool = False,
    exclude_ids: set[int] | None = None,
    exclude_subtree_of: int | None = None,
) -> list[Person]:
    conditions = [
        (
            scope_condition_for(user, Person.id)
            if full_only
            else visibility_condition(user)
        ),
        Person.status == PersonStatus.ACTIVE,
    ]
    if group_type is not None:
        conditions.append(Person.group_type == group_type)
    if leader_only:
        conditions.append(Person.group_type != GroupType.MEMBER)
        conditions.append(
            Person.id.not_in(
                select(User.leader_person_id).where(User.leader_person_id.is_not(None))
            )
        )
    if member_only:
        conditions.append(Person.group_type == GroupType.MEMBER)
        conditions.append(
            Person.id.not_in(
                select(User.leader_person_id).where(User.leader_person_id.is_not(None))
            )
        )
    if search and search.strip():
        term = search.strip()
        reg_term = re.sub(r"[\s\-_]", "", term).upper()
        name_conditions = [
            _fts_condition(Person.last_name, term),
            _fts_condition(Person.first_name, term),
        ]
        conditions.append(
            or_(
                Person.reg_number.ilike(f"{_escape_like(reg_term)}%", escape="\\"),
                *[condition for condition in name_conditions if condition is not None],
            )
        )
    if exclude_ids:
        conditions.append(Person.id.not_in(exclude_ids))
    if exclude_subtree_of is not None:
        conditions.append(
            ~exists().where(
                PersonClosure.ancestor_id == exclude_subtree_of,
                PersonClosure.descendant_id == Person.id,
            )
        )
    stmt = (
        select(Person)
        .where(*conditions)
        .order_by(Person.last_name.asc(), Person.first_name.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def scope_roots(db: Session, user: User) -> list[Person]:
    if is_admin(user):
        stmt = (
            select(Person)
            .where(Person.parent_id.is_(None), Person.status == PersonStatus.ACTIVE)
            .order_by(Person.last_name, Person.first_name)
            .limit(50)
        )
        return list(db.scalars(stmt))
    roots = scope_root_ids(user)
    if not roots:
        return []
    stmt = (
        select(Person)
        .where(
            Person.id.in_(roots),
            Person.status == PersonStatus.ACTIVE,
        )
        .order_by(Person.last_name, Person.first_name)
    )
    return list(db.scalars(stmt))


def member_counts(db: Session, parent_ids: list[int]) -> dict[int, int]:
    if not parent_ids:
        return {}
    stmt = (
        select(Person.parent_id, func.count())
        .where(Person.parent_id.in_(parent_ids), Person.status == PersonStatus.ACTIVE)
        .group_by(Person.parent_id)
    )
    return {row[0]: int(row[1]) for row in db.execute(stmt)}


def children_count(db: Session, person_id: int) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(Person).where(Person.parent_id == person_id)
        )
        or 0
    )


def is_in_subtree(db: Session, ancestor_id: int, descendant_id: int) -> bool:
    return (
        db.scalars(
            select(PersonClosure.ancestor_id).where(
                PersonClosure.ancestor_id == ancestor_id,
                PersonClosure.descendant_id == descendant_id,
            )
        ).first()
        is not None
    )


def leader_reference_exists(db: Session, person_id: int) -> bool:
    from app.models.user import User

    return db.scalars(select(User.id).where(User.leader_person_id == person_id)).first() is not None


def person_options(db: Session, ids: list[int]) -> list[Person]:
    if not ids:
        return []
    return list(
        db.scalars(
            select(Person)
            .options(selectinload(Person.creator))
            .where(Person.id.in_(ids))
        )
    )


def persons_by_ids(db: Session, ids: list[int]) -> dict[int, Person]:
    if not ids:
        return {}
    return {p.id: p for p in db.scalars(select(Person).where(Person.id.in_(ids)))}

