from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context
from app.core.database import get_db
from app.schemas.dashboard import DashboardStats
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
def get_dashboard(
    ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)
) -> DashboardStats:
    return dashboard_service.get_dashboard(db, ctx.user)
