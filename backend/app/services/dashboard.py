from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.time import local_today
from app.models.enums import Gender, GroupType
from app.models.user import User
from app.permissions import policy
from app.repositories import audit as audit_repo
from app.repositories import dashboard as dashboard_repo
from app.repositories import notifications as notifications_repo
from app.repositories import people as people_repo
from app.schemas.dashboard import (
    AgeBucket,
    DailyCount,
    DashboardStats,
    GenderCount,
    GroupCount,
    LabeledCount,
)
from app.services.audit_view import to_item
from app.services.serializers import person_summary


def _top_labeled(values: dict[str, int], limit: int = 8) -> list[LabeledCount]:
    ordered = sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [LabeledCount(name=name, count=int(count)) for name, count in ordered]


def get_dashboard(db: Session, user: User) -> DashboardStats:
    counts = dashboard_repo.counts(db, user)
    distribution = dashboard_repo.distribution_counts(db, user)
    group_counts = [
        GroupCount(group_type=group, count=int(distribution["groups"].get(group, 0)))
        for group in GroupType
    ]
    gender_counts = [
        GenderCount(gender=gender, count=int(distribution["genders"].get(gender, 0)))
        for gender in Gender
    ]
    district_counts = _top_labeled(distribution["districts"])
    khoroo_counts = _top_labeled(distribution["khoroos"])
    age_rows = dashboard_repo.age_counts(db, user)
    age_counts = [
        AgeBucket(label=label, min_age=minimum, max_age=maximum, count=int(age_rows.get(label, 0)))
        for label, minimum, maximum in dashboard_repo.AGE_BUCKETS
    ]
    if age_rows.get("unknown"):
        age_counts.append(
            AgeBucket(
                label="Тодорхойгүй",
                min_age=None,
                max_age=None,
                count=int(age_rows["unknown"]),
            )
        )
    daily_rows = dashboard_repo.daily_registrations(db, user)
    today = local_today()
    daily_registrations = [
        DailyCount(date=day, count=int(daily_rows.get(day, 0)))
        for day in (today - timedelta(days=offset) for offset in range(6, -1, -1))
    ]
    logs = (
        audit_repo.recent(db, limit=8)
        if policy.is_admin(user)
        else audit_repo.user_activity(db, user.id, limit=8)
    )
    recent = people_repo.recent_people(db, user, limit=5)
    scope_label = (
        "Бүх бүртгэл"
        if policy.is_admin(user)
        else ("Өөрийн мод" if user.leader_person_id else "Харьяалал оноогүй")
    )
    return DashboardStats(
        total_people=counts["total"],
        active_people=counts["active"],
        deleted_people=counts["deleted"],
        created_today=counts["today"],
        created_last_7_days=counts["week"],
        group_counts=group_counts,
        gender_counts=gender_counts,
        district_counts=district_counts,
        khoroo_counts=khoroo_counts,
        age_counts=age_counts,
        daily_registrations=daily_registrations,
        recent_people=[
            person_summary(
                person,
                sensitive=policy.can_view_sensitive(user),
                full=policy.can_view_full_person(db, user, person),
            )
            for person in recent
        ],
        recent_actions=[to_item(log) for log in logs],
        pending_imports=(
            dashboard_repo.pending_imports(db, user) if policy.can_import(user) else 0
        ),
        unread_notifications=notifications_repo.unread_count(db, user.id),
        scope_label=scope_label,
    )
