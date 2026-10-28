from app.models.enums import Gender
from app.models.person import Person
from app.models.user import User
from app.permissions import policy
from app.schemas.common import PersonRef, UserRef
from app.schemas.person import PersonDetail, PersonPermissions, PersonSummary


def mask_phone(phone: str | None) -> str | None:
    if not phone:
        return phone
    digits = phone.lstrip("+")
    if len(digits) <= 4:
        return "••••"
    return f"••••••{digits[-4:]}"


def mask_reg_number(reg_number: str) -> str:
    if len(reg_number) <= 4:
        return "••••"
    return f"{reg_number[:2]}••••{reg_number[-4:]}"


def person_ref(person: Person) -> PersonRef:
    return PersonRef(
        id=person.id,
        reg_number=person.reg_number,
        last_name=person.last_name,
        first_name=person.first_name,
        status=person.status.value,
    )


def user_ref(user: User | None) -> UserRef | None:
    if user is None:
        return None
    return UserRef(id=user.id, username=user.username, full_name=user.full_name)


def person_summary(
    person: Person, *, sensitive: bool, full: bool = True
) -> PersonSummary:
    return PersonSummary(
        id=person.id,
        reg_number=person.reg_number if full else mask_reg_number(person.reg_number),
        last_name=person.last_name,
        first_name=person.first_name,
        gender=person.gender if full else Gender.OTHER,
        birth_date=person.birth_date if full else None,
        phone=person.phone if sensitive else mask_phone(person.phone),
        district=person.district,
        khoroo=person.khoroo,
        group_type=person.group_type,
        parent_id=person.parent_id if full else None,
        status=person.status,
        full_profile=full,
        created_at=person.created_at,
        updated_at=person.updated_at,
    )


def person_detail(
    person: Person,
    *,
    viewer: User,
    path: list[Person],
    direct_member_count: int,
    creator: User | None = None,
    full: bool = True,
) -> PersonDetail:
    sensitive = policy.can_view_sensitive(viewer)
    parent = path[-1] if path else None
    return PersonDetail(
        id=person.id,
        reg_number=person.reg_number if full else mask_reg_number(person.reg_number),
        last_name=person.last_name,
        first_name=person.first_name,
        gender=person.gender if full else Gender.OTHER,
        birth_date=person.birth_date if full else None,
        phone=person.phone if sensitive else mask_phone(person.phone),
        district=person.district,
        khoroo=person.khoroo,
        group_type=person.group_type,
        parent_id=person.parent_id if full else None,
        status=person.status,
        full_profile=full,
        created_at=person.created_at,
        updated_at=person.updated_at,
        address=person.address if sensitive else None,
        job=person.job if full else None,
        created_by=user_ref(creator) if full else None,
        parent=person_ref(parent) if parent and full else None,
        path=[person_ref(item) for item in path] if full else [],
        direct_member_count=direct_member_count if full else 0,
        deleted_at=person.deleted_at if full else None,
        permissions=PersonPermissions(
            can_edit=policy.can_edit_person(viewer, person) and person.status.value == "ACTIVE",
            can_add_child=policy.can_add_child(viewer)
            and (policy.is_admin(viewer) or person.id == viewer.leader_person_id)
            and person.status.value == "ACTIVE",
            can_delete=policy.can_delete(viewer) and person.status.value == "ACTIVE",
            can_restore=policy.can_delete(viewer) and person.status.value == "DELETED",
            can_purge=policy.can_delete(viewer) and person.status.value == "DELETED",
            can_view_sensitive=sensitive,
            can_view_full=full,
            can_manage_account=policy.can_manage_account_for(viewer, person),
        ),
    )
