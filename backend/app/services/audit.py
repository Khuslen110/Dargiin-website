from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import audit as audit_repo


def log(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    metadata: dict[str, Any] | None = None,
    ip: str | None = None,
):
    return audit_repo.record(
        db,
        actor_id=actor.id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
        ip=ip,
    )
