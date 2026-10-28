from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import local_today
from app.models.enums import ImportStatus, PersonStatus
from app.models.import_job import ImportJob
from app.models.person import Person
from app.models.user import User
from app.permissions.policy import is_admin, scope_condition_for

AGE_BUCKETS = (
    ("0–17", 0, 17),
    ("18–24", 18, 24),
    ("25–34", 25, 34),
    ("35–44", 35, 44),
    ("45–54", 45, 54),
    ("55–64", 55, 64),
    ("65+", 65, None),
)


def counts(db: Session, user: User) -> dict[str, int]:
    tz = ZoneInfo(settings.timezone)
    today_start = datetime.combine(local_today(), time.min, tzinfo=tz)
    week_start = today_start - timedelta(days=6)
    stmt = (
        select(
            func.count().label("total"),
            func.count().filter(Person.status == PersonStatus.ACTIVE).label("active"),
            func.count().filter(Person.status == PersonStatus.DELETED).label("deleted"),
            func.count().filter(Person.created_at >= today_start).label("today"),
            func.count().filter(Person.created_at >= week_start).label("week"),
        )
        .select_from(Person)
        .where(scope_condition_for(user, Person.id))
    )
    row = db.execute(stmt).one()
    return {
        "total": row.total,
        "active": row.active,
        "deleted": row.deleted,
        "today": row.today,
        "week": row.week,
    }


def distribution_counts(db: Session, user: User) -> dict[str, dict]:
    stmt = (
        select(
            Person.group_type,
            Person.gender,
            Person.district,
            Person.khoroo,
            func.count().label("count"),
        )
        .where(scope_condition_for(user, Person.id), Person.status == PersonStatus.ACTIVE)
        .group_by(text("GROUPING SETS ((group_type), (gender), (district), (khoroo))"))
    )
    groups: dict = {}
    genders: dict = {}
    districts: dict[str, int] = {}
    khoroos: dict[str, int] = {}
    for row in db.execute(stmt):
        count = int(row.count)
        if row.group_type is not None:
            groups[row.group_type] = count
        elif row.gender is not None:
            genders[row.gender] = count
        elif row.district is not None:
            name = row.district.strip()
            if name:
                districts[name] = districts.get(name, 0) + count
        elif row.khoroo is not None:
            name = row.khoroo.strip()
            if name:
                khoroos[name] = khoroos.get(name, 0) + count
    return {
        "groups": groups,
        "genders": genders,
        "districts": districts,
        "khoroos": khoroos,
    }


def _years_before(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def age_counts(db: Session, user: User) -> dict[str, int]:
    today = local_today()
    cutoffs = {years: _years_before(today, years) for years in (18, 25, 35, 45, 55, 65)}
    unknown = (Person.birth_date.is_(None)) | (Person.birth_date > today)
    ranges = (
        ("0–17", Person.birth_date > cutoffs[18], Person.birth_date <= today),
        ("18–24", Person.birth_date > cutoffs[25], Person.birth_date <= cutoffs[18]),
        ("25–34", Person.birth_date > cutoffs[35], Person.birth_date <= cutoffs[25]),
        ("35–44", Person.birth_date > cutoffs[45], Person.birth_date <= cutoffs[35]),
        ("45–54", Person.birth_date > cutoffs[55], Person.birth_date <= cutoffs[45]),
        ("55–64", Person.birth_date > cutoffs[65], Person.birth_date <= cutoffs[55]),
        ("65+", Person.birth_date <= cutoffs[65]),
    )
    columns = [
        func.count().filter(*conditions).label(f"age_{index}")
        for index, (_, *conditions) in enumerate(ranges)
    ]
    columns.append(func.count().filter(unknown).label("unknown"))
    stmt = select(*columns).where(
        scope_condition_for(user, Person.id), Person.status == PersonStatus.ACTIVE
    )
    row = db.execute(stmt).one()
    result = {label: int(getattr(row, f"age_{index}")) for index, (label, *_) in enumerate(ranges)}
    result["unknown"] = int(row.unknown)
    return result


def daily_registrations(db: Session, user: User) -> dict:
    tz = ZoneInfo(settings.timezone)
    today_start = datetime.combine(local_today(), time.min, tzinfo=tz)
    week_start = today_start - timedelta(days=6)
    day = func.date(func.timezone(settings.timezone, Person.created_at))
    stmt = (
        select(day.label("day"), func.count().label("count"))
        .where(scope_condition_for(user, Person.id), Person.created_at >= week_start)
        .group_by(day)
    )
    return {row.day: row.count for row in db.execute(stmt)}


def pending_imports(db: Session, user: User) -> int:
    stmt = select(func.count()).select_from(ImportJob).where(
        ImportJob.status.in_([ImportStatus.PREVIEWED, ImportStatus.PROCESSING])
    )
    if not is_admin(user):
        stmt = stmt.where(ImportJob.user_id == user.id)
    return db.scalar(stmt) or 0
