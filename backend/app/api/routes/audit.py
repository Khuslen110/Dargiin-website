from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_admin
from app.core.database import get_db
from app.repositories import audit as audit_repo
from app.schemas.audit import AuditItem
from app.schemas.common import Page
from app.services.audit_view import to_item

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=Page[AuditItem])
def list_audit(
    ctx: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = None,
    actor_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Page[AuditItem]:
    logs, total = audit_repo.list_logs(
        db,
        page=page,
        page_size=page_size,
        action=action,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
    )
    return Page[AuditItem](
        items=[to_item(log) for log in logs],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size,
    )
