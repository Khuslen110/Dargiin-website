from app.models.audit import AuditLog
from app.schemas.audit import AuditActor, AuditItem


def to_item(log: AuditLog) -> AuditItem:
    actor = None
    if log.actor is not None:
        actor = AuditActor(
            id=log.actor.id, username=log.actor.username, full_name=log.actor.full_name
        )
    return AuditItem.from_model(log, actor)
