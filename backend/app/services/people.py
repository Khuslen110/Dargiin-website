from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit_actions import AuditAction
from app.core.errors import bad_request, conflict, forbidden, not_found
from app.core.group_rules import (
    PARENT_GROUP_TYPE,
    group_type_error,
    is_valid_child,
    next_group_type,
)
from app.core.time import birth_date_bounds_for_age
from app.core.validation import normalize_reg_number
from app.models.enums import Gender, GroupType, PersonStatus
from app.models.person import Person
from app.models.user import User
from app.permissions import policy
from app.repositories import hierarchy as hierarchy_repo
from app.repositories import people as people_repo
from app.schemas.person import (
    HierarchyNode,
    PersonCreate,
    PersonDetail,
    PersonSummary,
    PersonUpdate,
)
from app.services import audit as audit_service
from app.services.serializers import person_detail, person_summary


def _require_editor(actor: User) -> None:
    if not policy.can_edit(actor):
        raise forbidden("Танд хүний бүртгэл нэмэх эсвэл засах эрх байхгүй.")


def _parent_for_write(
    db: Session, actor: User, parent_id: int | None, *, required: bool
) -> Person | None:
    if parent_id is None:
        if required:
            raise bad_request(
                "Харьяалагдах хүнээ сонгоно уу.",
                fields={"parent_id": "Харьяалагдах хүн заавал шаардлагатай."},
            )
        return None
    parent = people_repo.get_visible_for_update(db, actor, parent_id)
    if parent is None or parent.status != PersonStatus.ACTIVE:
        raise bad_request(
            "Сонгосон харьяалагдах хүн олдсонгүй эсвэл таны харьяалалд байхгүй.",
            fields={"parent_id": "Хүчинтэй харьяалагдах хүн сонгоно уу."},
        )
    return parent


def _summary(db: Session, person: Person, viewer: User) -> PersonSummary:
    return person_summary(
        person,
        sensitive=policy.can_view_sensitive(viewer),
        full=policy.can_view_full_person(db, viewer, person),
    )


def _detail(db: Session, person: Person, viewer: User) -> PersonDetail:
    full = policy.can_view_full_person(db, viewer, person)
    path = people_repo.path_to_person(db, viewer, person.id) if full else []
    path = [item for item in path if policy.can_view_full_person(db, viewer, item)]
    return person_detail(
        person,
        viewer=viewer,
        path=path,
        direct_member_count=(
            people_repo.count_direct_members(db, person.id) if full else 0
        ),
        creator=person.creator,
        full=full,
    )


def _creation_parent(
    db: Session, actor: User, payload: PersonCreate
) -> Person | None:
    if policy.is_admin(actor):
        parent = _parent_for_write(
            db, actor, payload.parent_id, required=False
        )
        if parent is None:
            if payload.group_type != GroupType.TUMT:
                raise bad_request(
                    "Үндсэн бүртгэл зөвхөн Түмт төрөлтэй байна.",
                    fields={"group_type": "Эхний түвшин зөвхөн Түмт байна."},
                )
            return None
        if not is_valid_child(parent.group_type, payload.group_type):
            raise bad_request(
                group_type_error(parent.group_type),
                fields={"group_type": group_type_error(parent.group_type)},
            )
        return parent

    leader = policy.leader_person(actor)
    if leader is None or leader.status != PersonStatus.ACTIVE:
        raise forbidden("Танд удирдах хүн оноогүй байна. Админаас эрхээ аваарай.")
    expected = next_group_type(leader.group_type)
    if expected is None:
        raise forbidden("Гишүүн төрлийн хүн доор шинэ бүртгэл нэмэх боломжгүй.")
    if payload.parent_id is not None and payload.parent_id != leader.id:
        raise bad_request(
            "Та зөвхөн өөрийн шууд доор хүн нэмэх боломжтой.",
            fields={"parent_id": "Харьяалал өөрийн бүртгэл байх ёстой."},
        )
    if payload.group_type != expected:
        message = group_type_error(leader.group_type)
        raise bad_request(message, fields={"group_type": message})
    return leader


def _validate_group_change(
    db: Session, person: Person, parent: Person | None, group_type: GroupType
) -> None:
    if parent is None:
        if group_type != GroupType.TUMT:
            raise bad_request(
                "Үндсэн бүртгэл зөвхөн Түмт төрөлтэй байна.",
                fields={"group_type": "Эхний түвшин зөвхөн Түмт байна."},
            )
    elif not is_valid_child(parent.group_type, group_type):
        message = group_type_error(parent.group_type)
        raise bad_request(message, fields={"group_type": message})
    if group_type != person.group_type:
        child_groups = people_repo.child_group_types(db, person.id)
        invalid = [item for item in child_groups if not is_valid_child(group_type, item)]
        if invalid:
            raise conflict(
                "Доорх хүмүүсийн бүлгийн төрөл шинэ шатлалд тохирохгүй байна. "
                "Эхлээд тэдгээрийн төрлийг өөрчилнө үү.",
                code="INVALID_GROUP_CHANGE",
            )


def search_people(
    db: Session,
    viewer: User,
    *,
    page: int,
    page_size: int,
    reg_number: str | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
    phone: str | None = None,
    district: str | None = None,
    khoroo: str | None = None,
    address: str | None = None,
    job: str | None = None,
    gender: Gender | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    group_type: GroupType | None = None,
    under_person_id: int | None = None,
    direct_only: bool = False,
    status: PersonStatus = PersonStatus.ACTIVE,
    sort: str = "created_at",
    order: str = "desc",
) -> tuple[list[PersonSummary], int]:
    normalized_reg = normalize_reg_number(reg_number) if reg_number and reg_number.strip() else None
    if phone and phone.strip() and not policy.can_view_sensitive(viewer):
        raise forbidden("Утасны дугаараар хайх эрх танд байхгүй.")
    if status == PersonStatus.DELETED and not policy.is_admin(viewer):
        raise forbidden("Устгасан бүртгэлийг харах эрх танд байхгүй.")
    for value in (age_min, age_max):
        if value is not None and not 0 <= value <= 120:
            raise bad_request("Нас 0–120 хооронд байх ёстой.", fields={"age": "0–120."})
    if age_min is not None and age_max is not None and age_min > age_max:
        raise bad_request("Насны доод хязгаар дээд хязгаараас их байна.")
    if under_person_id is not None:
        anchor = people_repo.get_visible(db, viewer, under_person_id)
        if anchor is None:
            raise not_found("Сонгосон хүний бүртгэл олдсонгүй.")

    birth_date_from, birth_date_to = birth_date_bounds_for_age(age_min, age_max)

    people, total = people_repo.search_people(
        db,
        viewer,
        page=page,
        page_size=page_size,
        reg_number=normalized_reg,
        last_name=last_name,
        first_name=first_name,
        phone=phone,
        district=district,
        khoroo=khoroo,
        address=address,
        job=job,
        gender=gender,
        birth_date_from=birth_date_from,
        birth_date_to=birth_date_to,
        group_type=group_type,
        under_person_id=under_person_id,
        direct_only=direct_only,
        status=status,
        sort=sort,
        order=order,
    )
    return [_summary(db, person, viewer) for person in people], total


def serialize_list(
    db: Session, people: list[Person], viewer: User
) -> list[PersonSummary]:
    return [_summary(db, person, viewer) for person in people]


def get_detail(db: Session, viewer: User, person_id: int) -> PersonDetail:
    person = people_repo.get_visible(db, viewer, person_id, include_deleted=True)
    if person is None:
        raise not_found("Хүний бүртгэл олдсонгүй.")
    if person.status == PersonStatus.DELETED and not policy.is_admin(viewer):
        raise not_found("Хүний бүртгэл олдсонгүй.")
    return _detail(db, person, viewer)


def create_person(
    db: Session,
    actor: User,
    payload: PersonCreate,
    *,
    ip: str | None = None,
) -> PersonDetail:
    _require_editor(actor)
    parent = _creation_parent(db, actor, payload)
    reg_number = normalize_reg_number(payload.reg_number)
    if people_repo.register_number_taken(db, reg_number):
        raise conflict(
            "Энэ регистрийн дугаар аль хэдийн бүртгэгдсэн байна.",
            code="DUPLICATE_REG_NUMBER",
            fields={"reg_number": "Регистрийн дугаар давхцаж байна."},
        )

    person = Person(
        reg_number=reg_number,
        last_name=payload.last_name,
        first_name=payload.first_name,
        gender=payload.gender,
        birth_date=payload.birth_date,
        phone=payload.phone,
        district=payload.district,
        khoroo=payload.khoroo,
        address=payload.address,
        job=payload.job,
        group_type=payload.group_type,
        parent_id=parent.id if parent else None,
        created_by_id=actor.id,
        status=PersonStatus.ACTIVE,
    )
    db.add(person)
    try:
        db.flush()
        hierarchy_repo.add_person_to_closure(db, person.id, person.parent_id)
        audit_service.log(
            db,
            actor=actor,
            action=AuditAction.PERSON_CREATE,
            entity_type="person",
            entity_id=person.id,
            metadata={
                "group_type": person.group_type.value,
                "parent_id": person.parent_id,
            },
            ip=ip,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict(
            "Энэ регистрийн дугаар аль хэдийн бүртгэгдсэн байна.",
            code="DUPLICATE_REG_NUMBER",
            fields={"reg_number": "Регистрийн дугаар давхцаж байна."},
        ) from None

    person = people_repo.get_visible(db, actor, person.id, include_deleted=True)
    assert person is not None
    return _detail(db, person, actor)


def update_person(
    db: Session,
    actor: User,
    person_id: int,
    payload: PersonUpdate,
    *,
    ip: str | None = None,
) -> PersonDetail:
    _require_editor(actor)
    person = people_repo.get_visible_for_update(db, actor, person_id)
    if person is None:
        raise not_found("Хүний бүртгэл олдсонгүй.")
    if person.status != PersonStatus.ACTIVE:
        raise conflict("Устгасан бүртгэлийг засах боломжгүй. Эхлээд сэргээнэ үү.")

    if not policy.can_edit_person(actor, person):
        raise forbidden("Та зөвхөн өөрийн болон шууд доорх хүний мэдээллийг засах боломжтой.")

    fields = payload.model_fields_set
    if not policy.is_admin(actor):
        if "parent_id" in fields and payload.parent_id != person.parent_id:
            raise forbidden("Харьяаллыг зөвхөн администратор өөрчилнө.")
        if "group_type" in fields and payload.group_type != person.group_type:
            raise forbidden("Бүлгийн төрлийг зөвхөн администратор өөрчилнө.")

    parent_changed = False
    new_parent: Person | None = None
    new_group_type = (
        payload.group_type
        if "group_type" in fields and payload.group_type is not None
        else person.group_type
    )
    if policy.is_admin(actor):
        if "parent_id" in fields:
            new_parent_id = payload.parent_id
            if new_parent_id is None:
                new_parent = None
                if person.parent_id is not None:
                    parent_changed = True
            else:
                if new_parent_id == person.id:
                    raise bad_request("Хүн өөрөө өөрийнхөө харьяалагдах хүн байж болохгүй.")
                new_parent = _parent_for_write(db, actor, new_parent_id, required=True)
                assert new_parent is not None
                if hierarchy_repo.person_is_descendant(db, person.id, new_parent_id):
                    raise conflict(
                        "Харьяаллын цикл үүсгэх боломжгүй: сонгосон хүн таны засах хүний доор байна.",
                        code="CIRCULAR_HIERARCHY",
                    )
                if person.parent_id != new_parent_id:
                    parent_changed = True
        else:
            new_parent = (
                people_repo.get_any(db, person.parent_id) if person.parent_id else None
            )
        if "parent_id" in fields or "group_type" in fields:
            _validate_group_change(db, person, new_parent, new_group_type)

    changed: list[str] = []
    required_fields = {"last_name", "first_name", "gender", "group_type"}
    for attr in (
        "last_name",
        "first_name",
        "gender",
        "birth_date",
        "phone",
        "district",
        "khoroo",
        "address",
        "job",
        "group_type",
    ):
        if attr in fields:
            value = getattr(payload, attr)
            if value is None and attr in required_fields:
                raise bad_request("Энэ талбар хоосон байж болохгүй.", fields={attr: "Заавал бөглөнө."})
            if getattr(person, attr) != value:
                setattr(person, attr, value)
                changed.append(attr)

    if parent_changed:
        person.parent_id = new_parent.id if new_parent else None
        hierarchy_repo.move_subtree(db, person.id, person.parent_id)
        changed.append("parent_id")

    if not changed:
        raise bad_request("Өөрчлөгдсөн талбар байхгүй.")

    audit_service.log(
        db,
        actor=actor,
        action=(
            AuditAction.RELATIONSHIP_CHANGE if parent_changed else AuditAction.PERSON_UPDATE
        ),
        entity_type="person",
        entity_id=person.id,
        metadata={"changed": sorted(set(changed))},
        ip=ip,
    )
    db.commit()
    person = people_repo.get_visible(db, actor, person.id, include_deleted=True)
    assert person is not None
    return _detail(db, person, actor)


def soft_delete(
    db: Session, actor: User, person_id: int, *, ip: str | None = None
) -> None:
    if not policy.can_delete(actor):
        raise forbidden("Зөвхөн администратор бүртгэл устгах эрхтэй.")
    person = people_repo.get_any(db, person_id)
    if person is None:
        raise not_found("Хүний бүртгэл олдсонгүй.")
    if person.status == PersonStatus.DELETED:
        raise conflict("Энэ бүртгэл аль хэдийн устгагдсан байна.")
    from app.core.time import now_utc

    person.status = PersonStatus.DELETED
    person.deleted_at = now_utc()
    person.deleted_by_id = actor.id
    audit_service.log(
        db,
        actor=actor,
        action=AuditAction.PERSON_DELETE,
        entity_type="person",
        entity_id=person.id,
        metadata={"had_children": people_repo.children_count(db, person.id) > 0},
        ip=ip,
    )
    db.commit()


def restore(db: Session, actor: User, person_id: int, *, ip: str | None = None) -> PersonDetail:
    if not policy.can_delete(actor):
        raise forbidden("Зөвхөн администратор бүртгэл сэргээх эрхтэй.")
    person = people_repo.get_any(db, person_id)
    if person is None:
        raise not_found("Хүний бүртгэл олдсонгүй.")
    if person.status == PersonStatus.ACTIVE:
        raise conflict("Энэ бүртгэл аль хэдийн идэвхтэй байна.")
    person.status = PersonStatus.ACTIVE
    person.deleted_at = None
    person.deleted_by_id = None
    audit_service.log(
        db,
        actor=actor,
        action=AuditAction.PERSON_RESTORE,
        entity_type="person",
        entity_id=person.id,
        metadata={},
        ip=ip,
    )
    db.commit()
    person = people_repo.get_visible(db, actor, person.id, include_deleted=True)
    assert person is not None
    return _detail(db, person, actor)


def purge(
    db: Session,
    actor: User,
    person_id: int,
    *,
    confirm_reg_number: str,
    ip: str | None = None,
) -> None:
    if not policy.can_delete(actor):
        raise forbidden("Зөвхөн администратор бүр мөсөн устгах эрхтэй.")
    person = people_repo.get_any(db, person_id)
    if person is None:
        raise not_found("Хүний бүртгэл олдсонгүй.")
    if person.status != PersonStatus.DELETED:
        raise conflict("Эхлээд бүртгэлийг устгасан (soft delete) байх ёстой.")
    if normalize_reg_number(confirm_reg_number) != person.reg_number:
        raise bad_request("Регистрийн дугаар таарахгүй байна. Бүр мөсөн устгахыг цуцаллаа.")
    if people_repo.children_count(db, person.id) > 0:
        raise conflict(
            "Энэ хүнд шууд харьяалагдах хүн байгаа тул бүр мөсөн устгах "
            "боломжгүй. Эхлээд тэдгээрийг шилжүүлнэ үү."
        )
    if people_repo.leader_reference_exists(db, person.id):
        raise conflict(
            "Энэ хүн удирдагч хэрэглэгчтэй холбогдсон тул бүр мөсөн устгах боломжгүй."
        )

    hierarchy_repo.remove_from_closure(db, person.id)
    db.delete(person)
    audit_service.log(
        db,
        actor=actor,
        action=AuditAction.PERSON_PURGE,
        entity_type="person",
        entity_id=person_id,
        metadata={},
        ip=ip,
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict("Бүртгэлийг бүр мөсөн устгах боломжгүй: холбоотой өгөгдөл байна.") from None


def hierarchy_roots(db: Session, viewer: User) -> list[HierarchyNode]:
    roots = people_repo.scope_roots(db, viewer)
    if not roots:
        return []
    root_ids = [root.id for root in roots]
    counts = people_repo.member_counts(db, root_ids)
    return [
        HierarchyNode(
            **_summary(db, root, viewer).model_dump(),
            direct_member_count=counts.get(root.id, 0),
        )
        for root in roots
    ]


def parent_candidates(
    db: Session,
    viewer: User,
    *,
    search: str | None,
    exclude_person_id: int | None = None,
    child_group_type: GroupType | None = None,
    leader_only: bool = False,
) -> list[Person]:
    if not policy.can_edit(viewer):
        raise forbidden("Харьяалагдах хүн сонгох эрх танд байхгүй.")
    if child_group_type == GroupType.TUMT:
        return []
    parent_group_type = (
        PARENT_GROUP_TYPE.get(child_group_type)
        if child_group_type is not None
        else None
    )
    return people_repo.parent_candidates(
        db,
        viewer,
        search=search,
        group_type=parent_group_type,
        leader_only=leader_only,
        full_only=not policy.is_admin(viewer),
        exclude_ids={exclude_person_id} if exclude_person_id else None,
        exclude_subtree_of=exclude_person_id,
    )
