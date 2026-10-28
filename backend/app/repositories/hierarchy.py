from sqlalchemy import delete, func, insert, literal, select, true
from sqlalchemy.orm import Session

from app.models.person import Person, PersonClosure


def add_person_to_closure(db: Session, person_id: int, parent_id: int | None) -> None:
    db.execute(
        insert(PersonClosure).values(
            ancestor_id=person_id, descendant_id=person_id, depth=0
        )
    )
    if parent_id is None:
        return
    db.execute(
        insert(PersonClosure).from_select(
            ["ancestor_id", "descendant_id", "depth"],
            select(
                PersonClosure.ancestor_id,
                literal(person_id),
                PersonClosure.depth + 1,
            ).where(PersonClosure.descendant_id == parent_id),
        )
    )


def move_subtree(db: Session, person_id: int, new_parent_id: int | None) -> None:
    subtree = select(PersonClosure.descendant_id).where(
        PersonClosure.ancestor_id == person_id
    )
    db.execute(
        delete(PersonClosure).where(
            PersonClosure.descendant_id.in_(subtree),
            PersonClosure.ancestor_id.not_in(subtree),
        )
    )
    if new_parent_id is None:
        return
    ancestors = select(PersonClosure.ancestor_id, PersonClosure.depth).where(
        PersonClosure.descendant_id == new_parent_id
    ).subquery()
    descendants = (
        select(PersonClosure.descendant_id, PersonClosure.depth)
        .where(PersonClosure.ancestor_id == person_id)
        .subquery()
    )
    source = select(
        ancestors.c.ancestor_id,
        descendants.c.descendant_id,
        ancestors.c.depth + descendants.c.depth + 1,
    ).select_from(ancestors.join(descendants, true()))
    db.execute(
        insert(PersonClosure).from_select(
            ["ancestor_id", "descendant_id", "depth"], source
        )
    )


def remove_from_closure(db: Session, person_id: int) -> None:
    db.execute(
        delete(PersonClosure).where(
            (PersonClosure.ancestor_id == person_id)
            | (PersonClosure.descendant_id == person_id)
        )
    )


def subtree_size(db: Session, person_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(PersonClosure)
            .where(PersonClosure.ancestor_id == person_id)
        )
        or 0
    )


def subtree_person_ids(db: Session, person_id: int) -> list[int]:
    return list(
        db.scalars(
            select(PersonClosure.descendant_id).where(
                PersonClosure.ancestor_id == person_id
            )
        )
    )


def person_is_descendant(db: Session, ancestor_id: int, descendant_id: int) -> bool:
    return (
        db.scalars(
            select(PersonClosure.ancestor_id).where(
                PersonClosure.ancestor_id == ancestor_id,
                PersonClosure.descendant_id == descendant_id,
            )
        ).first()
        is not None
    )


def active_children_count(db: Session, person_id: int) -> int:
    return (
        db.scalar(
            select(func.count()).select_from(Person).where(Person.parent_id == person_id)
        )
        or 0
    )
