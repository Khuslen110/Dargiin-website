from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.enums import NotificationKind
from app.models.notification import Notification


def create(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str,
    kind: NotificationKind = NotificationKind.INFO,
) -> Notification:
    item = Notification(user_id=user_id, title=title, body=body, kind=kind)
    db.add(item)
    return item


def list_for_user(db: Session, user_id: int, *, limit: int = 20) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.read_at.is_(None).desc(), Notification.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def unread_count(db: Session, user_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
        or 0
    )


def mark_read(db: Session, user_id: int, notification_id: int) -> bool:
    result = db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(read_at=datetime.now(UTC))
    )
    return result.rowcount > 0


def mark_all_read(db: Session, user_id: int) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    return result.rowcount
