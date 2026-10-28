from sqlalchemy.orm import Session

from app.core.errors import conflict, forbidden, not_found
from app.models.enums import GroupType, PersonStatus, Role
from app.models.person import Person
from app.models.user import User
from app.permissions import policy
from app.repositories import people as people_repo
from app.repositories import users as users_repo
from app.schemas.user import PersonAccountCreate, UserCreate
from app.services import users as users_service


def _manageable_person(db: Session, actor: User, person_id: int) -> Person:
    person = people_repo.get_visible(db, actor, person_id, include_deleted=False)
    if person is None or person.status != PersonStatus.ACTIVE:
        raise not_found("Хүний бүртгэл олдсонгүй.")
    if not policy.can_manage_account_for(actor, person):
        raise forbidden(
            "Та зөвхөн өөрийн шууд доорх хүний нэвтрэх эрхийг удирдах боломжтой."
        )
    return person


def get_account(db: Session, actor: User, person_id: int) -> User | None:
    person = _manageable_person(db, actor, person_id)
    return users_repo.get_by_leader_person_id(db, person.id)


def create_account(
    db: Session,
    actor: User,
    person_id: int,
    payload: PersonAccountCreate,
    *,
    ip: str | None = None,
) -> User:
    person = _manageable_person(db, actor, person_id)
    if users_repo.get_by_leader_person_id(db, person.id) is not None:
        raise conflict("Энэ хүнд нэвтрэх эрх аль хэдийн үүссэн байна.")

    role = Role.MEMBER if person.group_type == GroupType.MEMBER else Role.LEADER
    return users_service.create_user(
        db,
        actor,
        UserCreate(
            username=payload.username,
            full_name=f"{person.last_name} {person.first_name}"[:120],
            password=payload.password,
            role=role,
            leader_person_id=person.id,
        ),
        ip=ip,
    )


def reset_account_password(
    db: Session,
    actor: User,
    person_id: int,
    new_password: str,
    *,
    ip: str | None = None,
) -> None:
    person = _manageable_person(db, actor, person_id)
    account = users_repo.get_by_leader_person_id(db, person.id)
    if account is None:
        raise not_found("Энэ хүнд нэвтрэх эрх үүсээгүй байна.")
    users_service.reset_password(db, actor, account.id, new_password, ip=ip)


__all__ = [
    "create_account",
    "get_account",
    "reset_account_password",
]
