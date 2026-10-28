from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, require_csrf
from app.core.database import get_db
from app.core.errors import not_found
from app.repositories import notifications as notifications_repo
from app.schemas.notification import NotificationList, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
def list_notifications(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
) -> NotificationList:
    items = notifications_repo.list_for_user(db, ctx.user.id, limit=limit)
    return NotificationList(
        items=[NotificationOut.model_validate(item) for item in items],
        unread_count=notifications_repo.unread_count(db, ctx.user.id),
    )


@router.post("/read-all")
def read_all(
    ctx: AuthContext = Depends(require_csrf), db: Session = Depends(get_db)
) -> dict[str, int]:
    updated = notifications_repo.mark_all_read(db, ctx.user.id)
    db.commit()
    return {"updated": updated}


@router.post("/{notification_id}/read")
def read_one(
    notification_id: int,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not notifications_repo.mark_read(db, ctx.user.id, notification_id):
        raise not_found("Мэдэгдэл олдсонгүй.")
    db.commit()
    return {"message": "Мэдэгдэл уншсан гэж тэмдэглэгдлээ."}
