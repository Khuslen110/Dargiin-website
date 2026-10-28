from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings


def now_utc() -> datetime:
    return datetime.now(UTC)


def local_today() -> date:
    return datetime.now(ZoneInfo(settings.timezone)).date()


def age_from_birth_date(birth_date: date | None, today: date | None = None) -> int | None:
    if birth_date is None:
        return None
    reference = today or local_today()
    years = reference.year - birth_date.year
    if (reference.month, reference.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def _shift_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def birth_date_bounds_for_age(
    min_age: int | None,
    max_age: int | None,
    today: date | None = None,
) -> tuple[date | None, date | None]:
    """Насны мужийг төрсөн огнооны хатуу хязгаарт хөрвүүлнэ."""
    reference = today or local_today()
    date_from: date | None = None
    date_to: date | None = None
    if max_age is not None:
        date_from = _shift_years(reference, -(max_age + 1)) + timedelta(days=1)
    if min_age is not None:
        date_to = _shift_years(reference, -min_age)
    return date_from, date_to
