from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context
from app.core.database import get_db
from app.schemas.person import HierarchyNode
from app.services import people as people_service

router = APIRouter(prefix="/hierarchy", tags=["hierarchy"])


@router.get("/roots", response_model=list[HierarchyNode])
def roots(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[HierarchyNode]:
    return people_service.hierarchy_roots(db, ctx.user)
