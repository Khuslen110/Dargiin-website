from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.audit import AuditLog
from app.schemas.common import ORMModel


class AuditActor(ORMModel):
    id: int
    username: str
    full_name: str


class AuditItem(BaseModel):
    id: int
    action: str
    actor: AuditActor | None
    entity_type: str | None
    entity_id: int | None
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def from_model(cls, log: AuditLog, actor: AuditActor | None) -> "AuditItem":
        return cls(
            id=log.id,
            action=log.action,
            actor=actor,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            metadata=log.meta or {},
            created_at=log.created_at,
        )


class AuditPage(BaseModel):
    items: list[AuditItem]
    page: int
    page_size: int
    total: int
    total_pages: int
