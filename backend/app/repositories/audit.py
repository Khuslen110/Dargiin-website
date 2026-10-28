from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.audit import AuditLog
from app.models.user import User


def record(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    metadata: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=metadata or {},
        ip=ip,
    )
    db.add(log)
    return log


def list_logs(
    db: Session,
    *,
    page: int,
    page_size: int,
    action: str | None = None,
    actor_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[AuditLog], int]:
    conditions = []
    if action:
        conditions.append(AuditLog.action == action)
    if actor_id is not None:
        conditions.append(AuditLog.actor_id == actor_id)
    if entity_type:
        conditions.append(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        conditions.append(AuditLog.entity_id == entity_id)
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    count_stmt = select(func.count()).select_from(AuditLog)
    stmt = select(AuditLog).options(joinedload(AuditLog.actor))
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
        stmt = stmt.where(condition)
    total = db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(stmt)), total


def recent(
    db: Session,
    *,
    limit: int,
    actor_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> list[AuditLog]:
    stmt = select(AuditLog).options(joinedload(AuditLog.actor))
    if actor_id is not None:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if entity_type is not None:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(limit)
    return list(db.scalars(stmt))


def actions_for_actor(db: Session, actor_id: int, limit: int = 8) -> list[AuditLog]:
    return recent(db, limit=limit, actor_id=actor_id)


def count_for_actor(db: Session, actor_id: int) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.actor_id == actor_id)
        )
        or 0
    )


def user_activity(db: Session, user_id: int, limit: int = 8) -> list[AuditLog]:
    from app.models.audit import AuditLog as _AuditLog

    stmt = (
        select(_AuditLog)
        .options(joinedload(_AuditLog.actor))
        .where(
            (_AuditLog.actor_id == user_id)
            | ((_AuditLog.entity_type == "user") & (_AuditLog.entity_id == user_id))
        )
        .order_by(_AuditLog.created_at.desc(), _AuditLog.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


__all__ = ["AuditLog", "User"]
