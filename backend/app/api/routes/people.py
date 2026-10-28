from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, client_ip, get_auth_context, require_admin_csrf, require_csrf
from app.core.database import get_db
from app.core.errors import not_found
from app.models.enums import Gender, GroupType, PersonStatus
from app.repositories import audit as audit_repo
from app.repositories import people as people_repo
from app.schemas.audit import AuditItem
from app.schemas.common import Page
from app.schemas.person import (
    HierarchyNode,
    ParentCandidate,
    PersonCreate,
    PersonDetail,
    PersonSummary,
    PersonUpdate,
    PurgeRequest,
)
from app.schemas.user import (
    PasswordResetRequest,
    PersonAccountCreate,
    PersonAccountOut,
    PersonAccountState,
)
from app.services import accounts as accounts_service
from app.services import people as people_service
from app.services.audit_view import to_item

router = APIRouter(prefix="/people", tags=["people"])

SortField = Literal[
    "created_at",
    "updated_at",
    "last_name",
    "first_name",
    "reg_number",
    "district",
    "khoroo",
    "group_type",
    "birth_date",
]


@router.get("", response_model=Page[PersonSummary])
def list_people(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    reg_number: str | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
    phone: str | None = None,
    district: str | None = None,
    khoroo: str | None = None,
    address: str | None = None,
    job: str | None = None,
    gender: Gender | None = None,
    age_min: int | None = Query(None, ge=0, le=120),
    age_max: int | None = Query(None, ge=0, le=120),
    group_type: GroupType | None = None,
    under_person_id: int | None = None,
    direct_only: bool = False,
    status: PersonStatus = PersonStatus.ACTIVE,
    sort: SortField = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> Page[PersonSummary]:
    items, total = people_service.search_people(
        db,
        ctx.user,
        page=page,
        page_size=page_size,
        reg_number=reg_number,
        last_name=last_name,
        first_name=first_name,
        phone=phone,
        district=district,
        khoroo=khoroo,
        address=address,
        job=job,
        gender=gender,
        age_min=age_min,
        age_max=age_max,
        group_type=group_type,
        under_person_id=under_person_id,
        direct_only=direct_only,
        status=status,
        sort=sort,
        order=order,
    )
    return Page[PersonSummary](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=PersonDetail, status_code=201)
def create_person(
    payload: PersonCreate,
    request: Request,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> PersonDetail:
    return people_service.create_person(
        db, ctx.user, payload, ip=client_ip(request)
    )


@router.get("/parent-candidates", response_model=list[ParentCandidate])
def parent_candidates(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    search: str | None = None,
    exclude_person_id: int | None = None,
    child_group_type: GroupType | None = None,
    leader_only: bool = False,
) -> list[ParentCandidate]:
    people = people_service.parent_candidates(
        db,
        ctx.user,
        search=search,
        exclude_person_id=exclude_person_id,
        child_group_type=child_group_type,
        leader_only=leader_only,
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


@router.get("/{person_id}", response_model=PersonDetail)
def get_person(
    person_id: int,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PersonDetail:
    return people_service.get_detail(db, ctx.user, person_id)


@router.patch("/{person_id}", response_model=PersonDetail)
def update_person(
    person_id: int,
    payload: PersonUpdate,
    request: Request,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> PersonDetail:
    return people_service.update_person(
        db, ctx.user, person_id, payload, ip=client_ip(request)
    )


@router.delete("/{person_id}")
def delete_person(
    person_id: int,
    request: Request,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    people_service.soft_delete(db, ctx.user, person_id, ip=client_ip(request))
    return {"message": "Бүртгэл устгагдлаа. Устгасан бүртгэлээс сэргээх боломжтой."}


@router.post("/{person_id}/restore", response_model=PersonDetail)
def restore_person(
    person_id: int,
    request: Request,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> PersonDetail:
    return people_service.restore(db, ctx.user, person_id, ip=client_ip(request))


@router.post("/{person_id}/purge")
def purge_person(
    person_id: int,
    payload: PurgeRequest,
    request: Request,
    ctx: AuthContext = Depends(require_admin_csrf),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    people_service.purge(
        db,
        ctx.user,
        person_id,
        confirm_reg_number=payload.confirm_reg_number,
        ip=client_ip(request),
    )
    return {"message": "Бүртгэл бүр мөсөн устгагдлаа."}


@router.get("/{person_id}/members", response_model=Page[HierarchyNode])
def direct_members(
    person_id: int,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> Page[PersonSummary]:
    people_service.get_detail(db, ctx.user, person_id)
    members, total = people_repo.direct_members(
        db, ctx.user, person_id, page=page, page_size=page_size
    )
    items = people_service.serialize_list(db, members, ctx.user)
    counts = people_repo.member_counts(db, [item.id for item in items])
    return Page[HierarchyNode](
        items=[
            HierarchyNode(**item.model_dump(), direct_member_count=counts.get(item.id, 0))
            for item in items
        ],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{person_id}/history", response_model=list[AuditItem])
def person_history(
    person_id: int,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
) -> list[AuditItem]:
    person = people_service.get_detail(db, ctx.user, person_id)
    if not person.full_profile:
        raise not_found("Энэ бүртгэлийн түүхийг харах эрх танд байхгүй.")
    logs = audit_repo.recent(
        db, limit=limit, entity_type="person", entity_id=person_id
    )
    return [to_item(log) for log in logs]


@router.get("/{person_id}/account", response_model=PersonAccountState)
def person_account(
    person_id: int,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PersonAccountState:
    account = accounts_service.get_account(db, ctx.user, person_id)
    return PersonAccountState(
        account=PersonAccountOut.model_validate(account) if account else None
    )


@router.post("/{person_id}/account", response_model=PersonAccountOut, status_code=201)
def create_person_account(
    person_id: int,
    payload: PersonAccountCreate,
    request: Request,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> PersonAccountOut:
    account = accounts_service.create_account(
        db, ctx.user, person_id, payload, ip=client_ip(request)
    )
    return PersonAccountOut.model_validate(account)


@router.post("/{person_id}/account/reset-password")
def reset_person_account_password(
    person_id: int,
    payload: PasswordResetRequest,
    request: Request,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    accounts_service.reset_account_password(
        db, ctx.user, person_id, payload.new_password, ip=client_ip(request)
    )
    return {"message": "Нууц үг шинэчлэгдэж, хэрэглэгчийн бүх идэвхтэй сесс хүчингүй боллоо."}
