from datetime import date

from pydantic import BaseModel

from app.models.enums import Gender, GroupType
from app.schemas.audit import AuditItem
from app.schemas.person import PersonSummary


class GroupCount(BaseModel):
    group_type: GroupType
    count: int


class GenderCount(BaseModel):
    gender: Gender
    count: int


class LabeledCount(BaseModel):
    name: str
    count: int


class AgeBucket(BaseModel):
    label: str
    min_age: int | None
    max_age: int | None
    count: int


class DailyCount(BaseModel):
    date: date
    count: int


class DashboardStats(BaseModel):
    total_people: int
    active_people: int
    deleted_people: int
    created_today: int
    created_last_7_days: int
    group_counts: list[GroupCount]
    gender_counts: list[GenderCount]
    district_counts: list[LabeledCount]
    khoroo_counts: list[LabeledCount]
    age_counts: list[AgeBucket]
    daily_registrations: list[DailyCount]
    recent_people: list[PersonSummary]
    recent_actions: list[AuditItem]
    pending_imports: int = 0
    unread_notifications: int = 0
    scope_label: str
