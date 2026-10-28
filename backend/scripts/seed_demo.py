"""Create a reproducible 100-person demo hierarchy with leader accounts.

Usage (from backend/):
    .venv/bin/python -m scripts.seed_demo
    .venv/bin/python -m scripts.seed_demo --admin admin --password 'Demo2026!Pass'
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.enums import Gender, GroupType, Role
from app.models.person import Person
from app.repositories import users as users_repo
from app.schemas.person import PersonCreate
from app.schemas.user import UserCreate
from app.services import people as people_service
from app.services import users as users_service

LAST_NAMES = [
    "Батбаяр", "Бор", "Ганбат", "Дорж", "Энхбат", "Эрдэнэ", "Гомбо", "Жамсран",
    "Лхагва", "Мөнх", "Намсрай", "Очир", "Пүрэв", "Содном", "Төмөр", "Цэрэн",
    "Чулуун", "Шарав", "Алтан", "Баатар",
]
FIRST_NAMES = [
    "Бат", "Болор", "Гантөмөр", "Дэлгэр", "Энхжин", "Эрдэнэбат", "Жаргал", "Лхагвасүрэн",
    "Мөнхбат", "Наран", "Оюун", "Пүрэвсүрэн", "Сараа", "Тэмүүлэн", "Ундрах", "Хүрэл",
    "Цэцэг", "Чинбат", "Шинэбаяр", "Ану", "Ариун", "Билгүүн", "Даваа", "Идэр",
]
JOBS = [
    "Инженер", "Багш", "Эмч", "Нягтлан", "Менежер", "Жолооч", "Худалдагч",
    "Программист", "Сэтгүүлч", "Хуульч", "Дизайнер", "Ажилтан",
]
DISTRICTS = [
    "Хан-Уул", "Баянзүрх", "Сүхбаатар", "Чингэлтэй", "Баянгол", "Сонгинохайрхан",
    "Налайх", "Багануур", "Хангарьд",
]
LEVEL_COUNTS = {
    GroupType.TUMT: 1,
    GroupType.MYANGAT: 3,
    GroupType.ZUUT: 9,
    GroupType.ARAVT: 18,
    GroupType.MEMBER: 69,
}
USERNAME_PREFIX = {
    GroupType.TUMT: "tumt",
    GroupType.MYANGAT: "myangat",
    GroupType.ZUUT: "zuut",
    GroupType.ARAVT: "aravt",
}


def _random_person(rng: random.Random, index: int, group_type: GroupType, parent_id: int | None):
    birth = date(1960, 1, 1) + timedelta(days=rng.randint(0, 45 * 365))
    return PersonCreate(
        reg_number=f"ДМ{index:08d}",
        last_name=rng.choice(LAST_NAMES),
        first_name=f"{rng.choice(FIRST_NAMES)}{index:02d}",
        gender=rng.choice([Gender.MALE, Gender.FEMALE]),
        birth_date=birth,
        phone=f"9{rng.randint(1000000, 9999999)}",
        district=rng.choice(DISTRICTS),
        khoroo=f"{rng.randint(1, 12)}-р хороо",
        address=f"{rng.randint(1, 25)}-р байр, {rng.randint(1, 80)} тоот",
        job=rng.choice(JOBS),
        group_type=group_type,
        parent_id=parent_id,
    )


def _existing_person(db, reg_number: str) -> Person | None:
    return db.scalar(select(Person).where(Person.reg_number == reg_number))


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed 100 demo people and leader accounts")
    parser.add_argument("--admin", default="admin", help="Existing admin username (default: admin)")
    parser.add_argument("--password", default="Demo2026!Pass", help="Password for generated leader accounts")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    with SessionLocal() as db:
        admin = users_repo.get_by_username(db, args.admin)
        if admin is None or admin.role != Role.ADMIN:
            print(
                f"Admin '{args.admin}' олдсонгүй. Эхлээд create-admin командыг ажиллуулна уу.",
                file=sys.stderr,
            )
            return 1

        created_people = 0
        created_users = 0
        index = 0
        parents = {GroupType.TUMT: [None]}
        leader_rows: dict[GroupType, list[Person]] = {}

        ordered_levels = (
            GroupType.TUMT,
            GroupType.MYANGAT,
            GroupType.ZUUT,
            GroupType.ARAVT,
            GroupType.MEMBER,
        )
        for level_position, group_type in enumerate(ordered_levels):
            parent_pool = parents[ordered_levels[level_position - 1]] if level_position else [None]
            persons: list[Person] = []
            for position in range(LEVEL_COUNTS[group_type]):
                index += 1
                parent_id = (
                    None
                    if group_type == GroupType.TUMT
                    else parent_pool[(position + index) % len(parent_pool)]
                )
                reg = f"ДМ{index:08d}"
                person = _existing_person(db, reg)
                if person is None:
                    try:
                        detail = people_service.create_person(
                            db, admin, _random_person(rng, index, group_type, parent_id)
                        )
                    except Exception as exc:  # pragma: no cover - CLI feedback
                        print(f"{reg} үүсгэхэд алдаа: {exc}", file=sys.stderr)
                        return 2
                    person = db.get(Person, detail.id)
                    created_people += 1
                assert person is not None
                persons.append(person)
            parents[group_type] = [person.id for person in persons]
            if group_type != GroupType.MEMBER:
                leader_rows[group_type] = persons

        for group_type, persons in leader_rows.items():
            prefix = USERNAME_PREFIX[group_type]
            for number, person in enumerate(persons, start=1):
                username = f"{prefix}.{number:02d}"
                if users_repo.username_exists(db, username):
                    continue
                payload = UserCreate(
                    username=username,
                    full_name=f"{person.last_name} {person.first_name}",
                    password=args.password,
                    role=Role.LEADER,
                    leader_person_id=person.id,
                )
                try:
                    users_service.create_user(db, admin, payload)
                except Exception as exc:  # pragma: no cover - CLI feedback
                    print(f"{username} хэрэглэгч үүсгэхэд алдаа: {exc}", file=sys.stderr)
                    return 2
                created_users += 1

        print("Demo өгөгдөл бэлэн.")
        print(f"  Шинэ хүн: {created_people}")
        print(f"  Шинэ удирдагч хэрэглэгч: {created_users}")
        print(f"  Нийт demo хүн: {index}")
        print("  Нэвтрэх нэр: tumt.01, myangat.01–03, zuut.01–09, aravt.01–18")
        print(f"  Нэгдсэн нууц үг: {args.password}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
