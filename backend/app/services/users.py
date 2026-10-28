from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit_actions import AuditAction
from app.core.errors import bad_request, conflict, forbidden, not_found
from app.core.group_rules import can_be_leader
from app.core.security import hash_password, password_policy_errors
from app.models.enums import GroupType, NotificationKind, PersonStatus, Role
from app.models.person import Person
from app.models.user import User
from app.repositories import notifications as notifications_repo
from app.repositories import people as people_repo
from app.repositories import users as users_repo
from app.schemas.user import UserCreate, UserUpdate
from app.services import audit as audit_service


def _validate_leader(
    db: Session, leader_person_id: int, *, exclude_user_id: int | None = None
) -> Person:
    leader = people_repo.get_any(db, leader_person_id)
    if leader is None or leader.status != PersonStatus.ACTIVE:
        raise bad_request(
            "Удирдах хүн олдсонгүй эсвэл идэвхгүй байна.",
            fields={"leader_person_id": "Идэвхтэй хүн сонгоно уу."},
        )
    if not can_be_leader(leader.group_type):
        raise bad_request(
            "Гишүүн төрлийн хүнд удирдах эрх оноох боломжгүй.",
            fields={"leader_person_id": "Түмт, Мянгат, Зуут эсвэл Аравт сонгоно уу."},
        )
    if users_repo.leader_person_taken(db, leader.id, exclude_user_id=exclude_user_id):
        raise conflict(
            "Энэ хүнд удирдагчийн хэрэглэгч аль хэдийн холбогдсон байна.",
            fields={"leader_person_id": "Өөр хүн сонгоно уу."},
        )
    return leader


def _validate_member(
    db: Session, member_person_id: int, *, exclude_user_id: int | None = None
) -> Person:
    member = people_repo.get_any(db, member_person_id)
    if member is None or member.status != PersonStatus.ACTIVE:
        raise bad_request(
            "Гишүүн олдсонгүй эсвэл идэвхгүй байна.",
            fields={"leader_person_id": "Идэвхтэй гишүүн сонгоно уу."},
        )
    if member.group_type != GroupType.MEMBER:
        raise bad_request(
            "Зөвхөн гишүүн төрлийн хүнд гишүүний эрх оноох боломжтой.",
            fields={"leader_person_id": "Гишүүн сонгоно уу."},
        )
    if users_repo.leader_person_taken(db, member.id, exclude_user_id=exclude_user_id):
        raise conflict(
            "Энэ гишүүнд хэрэглэгч аль хэдийн холбогдсон байна.",
            fields={"leader_person_id": "Өөр гишүүн сонгоно уу."},
        )
    return member


def _binding_for_role(
    db: Session,
    role: Role,
    leader_person_id: int | None,
    *,
    exclude_user_id: int | None = None,
) -> int | None:
    if role == Role.ADMIN:
        return None
    if leader_person_id is None:
        message = (
            "Гишүүн хэрэглэгчид гишүүн шаардлагатай."
            if role == Role.MEMBER
            else "Удирдагч хэрэглэгчид удирдах хүн шаардлагатай."
        )
        field_message = (
            "Гишүүнээ сонгоно уу."
            if role == Role.MEMBER
            else "Удирдах хүнээ сонгоно уу."
        )
        raise bad_request(message, fields={"leader_person_id": field_message})
    if role == Role.MEMBER:
        return _validate_member(
            db, leader_person_id, exclude_user_id=exclude_user_id
        ).id
    return _validate_leader(
        db, leader_person_id, exclude_user_id=exclude_user_id
    ).id


def _validate_password(password: str) -> None:
    errors = password_policy_errors(password)
    if errors:
        raise bad_request(" ".join(errors), fields={"password": " ".join(errors)})


def list_users(
    db: Session, *, page: int, page_size: int, search: str | None
) -> tuple[list[User], int]:
    return users_repo.list_users(db, page=page, page_size=page_size, search=search)


def create_user(
    db: Session, actor: User, payload: UserCreate, *, ip: str | None = None
) -> User:
    _validate_password(payload.password)
    if users_repo.username_exists(db, payload.username):
        raise conflict(
            "Энэ хэрэглэгчийн нэр аль хэдийн бүртгэгдсэн.",
            fields={"username": "Хэрэглэгчийн нэр давхцаж байна."},
        )

    leader_id = _binding_for_role(db, payload.role, payload.leader_person_id)

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        leader_person_id=leader_id,
        is_active=True,
    )
    db.add(user)
    try:
        db.flush()
        audit_service.log(
            db,
            actor=actor,
            action=AuditAction.USER_CREATE,
            entity_type="user",
            entity_id=user.id,
            metadata={"role": payload.role.value, "leader_person_id": leader_id},
            ip=ip,
        )
        notifications_repo.create(
            db,
            user_id=user.id,
            title="Тавтай морилно уу",
            body="Танд энэ системд нэвтрэх эрх үүслээ. Нууц үгээ Тохиргоо хэсгээс солих боломжтой.",
            kind=NotificationKind.INFO,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict(
            "Хэрэглэгчийн нэр аль хэдийн бүртгэгдсэн.",
            fields={"username": "Хэрэглэгчийн нэр давхцаж байна."},
        ) from None
    return users_repo.get_by_id(db, user.id)  # type: ignore[return-value]


def update_user(
    db: Session,
    actor: User,
    target_id: int,
    payload: UserUpdate,
    *,
    ip: str | None = None,
) -> User:
    target = users_repo.get_by_id(db, target_id)
    if target is None:
        raise not_found("Хэрэглэгч олдсонгүй.")

    fields = payload.model_fields_set
    privileged_fields = {"role", "is_active", "leader_person_id"}
    if actor.id == target.id and fields & privileged_fields:
        raise forbidden("Өөрийн эрх, удирдах хүн, төлөвийг өөрчлөх боломжгүй.")

    new_role = payload.role if "role" in fields and payload.role else target.role
    new_active = (
        payload.is_active
        if "is_active" in fields and payload.is_active is not None
        else target.is_active
    )

    if target.role == Role.ADMIN and target.is_active and (
        new_role != Role.ADMIN or not new_active
    ):
        if users_repo.count_active_admins(db) <= 1:
            raise conflict("Сүүлийн идэвхтэй администраторыг идэвхгүй болгох эсвэл эрх бууруулах боломжгүй.")

    bound_person_id = (
        payload.leader_person_id
        if "leader_person_id" in fields
        else target.leader_person_id
    )
    leader_id = _binding_for_role(
        db, new_role, bound_person_id, exclude_user_id=target.id
    )

    changed: list[str] = []
    if "full_name" in fields and payload.full_name is not None:
        if target.full_name != payload.full_name:
            target.full_name = payload.full_name
            changed.append("full_name")
    if "is_active" in fields and payload.is_active is not None:
        if target.is_active != payload.is_active:
            target.is_active = payload.is_active
            changed.append("is_active")
    if new_role != target.role:
        target.role = new_role
        changed.append("role")
    if target.leader_person_id != leader_id:
        target.leader_person_id = leader_id
        target.leader_person = None
        changed.append("leader_person_id")

    if target.is_active is False:
        users_repo.revoke_user_sessions(db, target.id)

    audit_service.log(
        db,
        actor=actor,
        action=AuditAction.USER_UPDATE,
        entity_type="user",
        entity_id=target.id,
        metadata={"changed": changed},
        ip=ip,
    )
    if changed and actor.id != target.id:
        notifications_repo.create(
            db,
            user_id=target.id,
            title="Бүртгэлийн мэдээлэл шинэчлэгдлээ",
            body="Таны хэрэглэгчийн эрх эсвэл мэдээллийг администратор шинэчилсэн.",
            kind=NotificationKind.INFO,
        )
    db.commit()
    return users_repo.get_by_id(db, target.id)  # type: ignore[return-value]


def reset_password(
    db: Session,
    actor: User,
    target_id: int,
    new_password: str,
    *,
    ip: str | None = None,
) -> None:
    if actor.id == target_id:
        raise forbidden("Өөрийн нууц үгийг Тохиргоо хэсгээс солино уу.")
    _validate_password(new_password)
    target = users_repo.get_by_id(db, target_id)
    if target is None:
        raise not_found("Хэрэглэгч олдсонгүй.")
    target.password_hash = hash_password(new_password)
    users_repo.revoke_user_sessions(db, target.id)
    audit_service.log(
        db,
        actor=actor,
        action=AuditAction.USER_PASSWORD_RESET,
        entity_type="user",
        entity_id=target.id,
        metadata={},
        ip=ip,
    )
    notifications_repo.create(
        db,
        user_id=target.id,
        title="Нууц үг шинэчлэгдлээ",
        body="Таны нууц үгийг эрх бүхий хэрэглэгч шинэчилсэн. Шинэ нууц үгээр дахин нэвтэрнэ үү.",
        kind=NotificationKind.WARNING,
    )
    db.commit()
