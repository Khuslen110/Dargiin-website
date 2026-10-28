from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import (
    AuthContext,
    client_ip,
    require_admin,
    require_admin_csrf,
)
from app.core.database import get_db
from app.models.enums import Role
from app.repositories import people as people_repo
from app.schemas.common import Page
from app.schemas.person import ParentCandidate
from app.schemas.user import (
    PasswordResetRequest,
    UserCreate,
    UserListItem,
    UserUpdate,
)
from app.services import users as users_service

router = APIRouter(prefix="/users", tags=["users"])


def _to_item(user) -> UserListItem:
    return UserListItem.model_validate(user)


@router.get("", response_model=Page[UserListItem])
def list_users(
    ctx: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
) -> Page[UserListItem]:
    users, total = users_service.list_users(
        db, page=page, page_size=page_size, search=search
    )
    return Page[UserListItem](
        items=[_to_item(user) for user in users],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/leader-candidates", response_model=list[ParentCandidate])
def leader_candidates(
    ctx: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    search: str | None = None,
    limit: int = Query(20, ge=1, le=50),
) -> list[ParentCandidate]:
    people = people_repo.parent_candidates(
        db,
        ctx.user,
        search=search,
        limit=limit,
        leader_only=True,
    )
    return [
        ParentCandidate(
            id=person.id,
            reg_number=person.reg_number,
            last_name=person.last_name,
            first_name=person.first_name,
            group_type=person.group_type,
        )
        for person in people
    ]


@router.get("/member-candidates", response_model=list[ParentCandidate])
def member_candidates(
    ctx: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    search: str | None = None,
    limit: int = Query(20, ge=1, le=50),
) -> list[ParentCandidate]:
    people = people_repo.parent_candidates(
        db,
        ctx.user,
        search=search,
        limit=limit,
        member_only=True,
    )
    return [
        ParentCandidate(
            id=person.id,
            reg_number=person.reg_number,
            last_name=person.last_name,
            first_name=person.first_name,
            group_type=person.group_type,
        )
        for person in people
    ]


@router.post("", response_model=UserListItem, status_code=201)
def create_user(
    payload: UserCreate,
    request: Request,
    ctx: AuthContext = Depends(require_admin_csrf),
    db: Session = Depends(get_db),
) -> UserListItem:
    user = users_service.create_user(
        db, ctx.user, payload, ip=client_ip(request)
    )
    return _to_item(user)


@router.patch("/{user_id}", response_model=UserListItem)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    ctx: AuthContext = Depends(require_admin_csrf),
    db: Session = Depends(get_db),
) -> UserListItem:
    user = users_service.update_user(
        db, ctx.user, user_id, payload, ip=client_ip(request)
    )
    return _to_item(user)


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: PasswordResetRequest,
    request: Request,
    ctx: AuthContext = Depends(require_admin_csrf),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    users_service.reset_password(
        db, ctx.user, user_id, payload.new_password, ip=client_ip(request)
    )
    return {"message": "Нууц үг шинэчлэгдэж, хэрэглэгчийн бүх идэвхтэй сесс хүчингүй боллоо."}


@router.get("/roles")
def roles(ctx: AuthContext = Depends(require_admin)) -> list[dict[str, str]]:
    return [
        {"value": Role.ADMIN.value, "label": "Администратор"},
        {"value": Role.LEADER.value, "label": "Удирдагч"},
        {"value": Role.MEMBER.value, "label": "Гишүүн"},
    ]
