from sqlalchemy import ColumnElement, false, select, true

from app.core.group_rules import NEXT_GROUP_TYPE
from app.models.enums import GroupType, PersonStatus
from app.models.person import Person, PersonClosure
from app.models.user import User
from app.schemas.auth import PermissionSet


def is_admin(user: User) -> bool:
    return user.role.value == "ADMIN"


def is_member(user: User) -> bool:
    return user.role.value == "MEMBER"


def scope_root_ids(user: User) -> list[int]:
    if is_admin(user):
        return []
    person = leader_person(user)
    if person is None:
        return []
    if is_member(user) and person.parent_id is not None:
        return [person.parent_id]
    return [person.id]


def leader_person(user: User) -> Person | None:
    return user.leader_person


def leader_group_type(user: User):
    person = leader_person(user)
    return person.group_type if person else None


def can_add_child(user: User) -> bool:
    if is_admin(user):
        return True
    group_type = leader_group_type(user)
    return can_edit(user) and group_type is not None and NEXT_GROUP_TYPE.get(group_type) is not None


def can_edit_person(user: User, person: Person) -> bool:
    if not can_edit(user):
        return False
    if is_admin(user):
        return True
    leader_id = user.leader_person_id
    if leader_id is None:
        return False
    return person.id == leader_id or person.parent_id == leader_id


def can_manage_account_for(user: User, person: Person) -> bool:
    if person.status != PersonStatus.ACTIVE:
        return False
    if is_admin(user):
        return True
    if not can_edit(user) or is_member(user):
        return False
    leader_id = user.leader_person_id
    if leader_id is None:
        return False
    return person.id != leader_id and person.parent_id == leader_id


def can_view_full_person(db, user: User, person: Person) -> bool:
    if is_admin(user):
        return True
    if person.status != PersonStatus.ACTIVE:
        return False
    leader_id = user.leader_person_id
    if leader_id is None:
        return False
    if person.id == leader_id:
        return True
    if is_member(user):
        return False
    if leader_group_type(user) == GroupType.TUMT:
        return True
    return (
        db.scalars(
            select(PersonClosure.ancestor_id).where(
                PersonClosure.ancestor_id == leader_id,
                PersonClosure.descendant_id == person.id,
            )
        ).first()
        is not None
    )


def scope_condition_for(user: User, person_id_col) -> ColumnElement[bool]:
    """Dashboard болон өөрийн модны статистикт хэрэглэх хүрээ."""
    if is_admin(user):
        return true()
    person = leader_person(user)
    if person is None:
        return false()
    if leader_group_type(user) == GroupType.TUMT:
        return true()
    root_id = person.parent_id if is_member(user) and person.parent_id else person.id
    return person_id_col.in_(
        select(PersonClosure.descendant_id).where(
            PersonClosure.ancestor_id == root_id
        )
    )


def visibility_condition_for(user: User, person_id_col) -> ColumnElement[bool]:
    """Тухайн person id баганад хэрэглэх scope нөхцөл."""
    if is_admin(user):
        return true()
    if leader_person(user) is None:
        return false()
    if is_member(user):
        roots = scope_root_ids(user)
        if not roots:
            return false()
        return person_id_col.in_(
            select(PersonClosure.descendant_id).where(
                PersonClosure.ancestor_id.in_(roots)
            )
        )
    return true()


def visibility_condition(user: User) -> ColumnElement[bool]:
    return visibility_condition_for(user, Person.id)


def can_view_sensitive(user: User) -> bool:
    return is_admin(user) or user.leader_person_id is not None


def can_edit(user: User) -> bool:
    return is_admin(user) or (
        user.role.value == "LEADER" and user.leader_person_id is not None
    )


def can_import(user: User) -> bool:
    return is_admin(user)


def can_export(user: User) -> bool:
    return is_admin(user)


def can_delete(user: User) -> bool:
    return is_admin(user)


def permission_set(user: User) -> PermissionSet:
    return PermissionSet(
        can_edit=can_edit(user),
        can_import=can_import(user),
        can_export=can_export(user),
        can_view_sensitive=can_view_sensitive(user),
        can_delete=can_delete(user),
        can_manage_users=is_admin(user),
        can_add_child=can_add_child(user),
    )

