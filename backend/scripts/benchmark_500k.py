"""500,000 бүртгэлтэй үед үндсэн query-үүдийн гүйцэтгэлийг хэмжинэ.

Хэрэглэх:
    createdb people_registry_bench
    cd backend
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/people_registry_bench \
        .venv/bin/alembic upgrade head
    DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/people_registry_bench \
        .venv/bin/python scripts/benchmark_500k.py

Дахин ажиллуулахад өгөгдөл байгаа бол дахин үүсгэхгүй. ``--force`` өгвөл
бүртгэлүүдийг устгаж дахин үүсгэнэ.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.models.enums import PersonStatus  # noqa: E402
from app.repositories import people as people_repo  # noqa: E402

TOTAL = 500_000
ROOTS = 50
MYANGAT = 500
ZUUT = 5_000
ARAVT = 50_000

LAST_NAMES = [
    "Бат", "Дорж", "Сүх", "Ганбат", "Эрдэнэ", "Мөнх", "Оюун", "Нармандах",
    "Алтан", "Цэрэн", "Баяр", "Хүрэл", "Төмөр", "Болд", "Сайн", "Жаргал",
    "Отгон", "Уран", "Хонгор", "Наран",
]
FIRST_NAMES = [
    "Сүхбат", "Долгор", "Энхбат", "Ариунаа", "Тэмүүлэн", "Болормаа",
    "Мөнхбат", "Саран", "Түвшин", "Оюунаа", "Батбаяр", "Хулан",
    "Гантулга", "Номин", "Эрдэнэбат", "Сэлэнгэ", "Амар", "Жавхлан",
    "Хишиг", "Ану",
]
DISTRICTS = [
    "Хан-Уул", "Баянзүрх", "Сүхбаатар", "Чингэлтэй", "Баянгол",
    "Сонгинохайрхан", "Налайх", "Багануур", "Хангарьд",
]


def parent_for(person_id: int) -> int | None:
    if person_id <= ROOTS:
        return None
    if person_id <= ROOTS + MYANGAT:
        return 1 + (person_id - ROOTS - 1) // 10
    if person_id <= ROOTS + MYANGAT + ZUUT:
        return ROOTS + 1 + (person_id - ROOTS - MYANGAT - 1) // 10
    if person_id <= ROOTS + MYANGAT + ZUUT + ARAVT:
        return (
            ROOTS + MYANGAT + 1
            + (person_id - ROOTS - MYANGAT - ZUUT - 1) // 10
        )
    return (
        ROOTS + MYANGAT + ZUUT + 1
        + ((person_id - (ROOTS + MYANGAT + ZUUT + ARAVT) - 1) % ARAVT)
    )


def group_for(person_id: int) -> str:
    if person_id <= ROOTS:
        return "TUMT"
    if person_id <= ROOTS + MYANGAT:
        return "MYANGAT"
    if person_id <= ROOTS + MYANGAT + ZUUT:
        return "ZUUT"
    if person_id <= ROOTS + MYANGAT + ZUUT + ARAVT:
        return "ARAVT"
    return "MEMBER"


def seed(conn) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    base_birth = date(1950, 1, 1)

    dbapi = conn.connection
    with dbapi.cursor() as cur:
        cur.execute("TRUNCATE person_closure, people, user_sessions CASCADE")
        cur.execute("TRUNCATE users RESTART IDENTITY CASCADE")
        cur.execute(
            """
            INSERT INTO users (id, username, full_name, password_hash, role)
            VALUES (1, 'benchmark', 'Benchmark Admin', 'not-a-real-hash', 'ADMIN')
            """
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        for person_id in range(1, TOTAL + 1):
            parent_id = parent_for(person_id)
            group = group_for(person_id)
            last_name = LAST_NAMES[person_id % len(LAST_NAMES)]
            first_name = FIRST_NAMES[(person_id * 7) % len(FIRST_NAMES)]
            gender = "MALE" if person_id % 2 == 0 else "FEMALE"
            birth = base_birth + timedelta(days=person_id % 25_000)
            phone = f"+976{person_id:08d}"
            district = DISTRICTS[person_id % len(DISTRICTS)]
            khoroo = f"{person_id % 30 + 1}-р хороо"
            created = now - timedelta(days=person_id % 365)
            writer.writerow(
                [
                    person_id,
                    f"БН{person_id:08d}",
                    last_name,
                    first_name,
                    gender,
                    birth.isoformat(),
                    phone,
                    district,
                    khoroo,
                    f"{district}, {khoroo}, {person_id % 100} тоот",
                    "Инженер" if person_id % 3 == 0 else "Багш",
                    group,
                    "" if parent_id is None else parent_id,
                    1,
                    "ACTIVE",
                    created.isoformat(),
                    created.isoformat(),
                ]
            )
            if person_id % 50_000 == 0:
                print(f"  мөр бэлдэж байна: {person_id:,}")

        buffer.seek(0)
        columns = (
            "id, reg_number, last_name, first_name, gender, birth_date, phone, "
            "district, khoroo, address, job, group_type, parent_id, created_by_id, "
            "status, created_at, updated_at"
        )
        with cur.copy(f"COPY people ({columns}) FROM STDIN WITH (FORMAT csv)") as copy:
            for chunk in iter(lambda: buffer.read(4 * 1024 * 1024), ""):
                copy.write(chunk)
        cur.execute("SELECT setval('people_id_seq', %s, true)", (TOTAL,))

        print("  closure table үүсгэж байна…")
        cur.execute("SET LOCAL work_mem = '256MB'")
        cur.execute(
            """
            INSERT INTO person_closure (ancestor_id, descendant_id, depth)
            WITH RECURSIVE ancestors AS (
                SELECT id AS descendant_id, id AS ancestor_id, 0 AS depth
                FROM people
                UNION ALL
                SELECT a.descendant_id, p.parent_id, a.depth + 1
                FROM ancestors a
                JOIN people p ON p.id = a.ancestor_id
                WHERE p.parent_id IS NOT NULL
            )
            SELECT ancestor_id, descendant_id, depth FROM ancestors
            """
        )
        cur.execute("ANALYZE people")
        cur.execute("ANALYZE person_closure")
        cur.execute("SELECT count(*) FROM people")
        print(f"  нийт бүртгэл: {cur.fetchone()[0]:,}")
        cur.execute("SELECT count(*) FROM person_closure")
        print(f"  closure мөр: {cur.fetchone()[0]:,}")


def admin_user():
    return SimpleNamespace(
        id=1,
        role=SimpleNamespace(value="ADMIN"),
        leader_person_id=None,
        leader_person=None,
    )


def scoped_user(root_id: int = 1):
    return SimpleNamespace(
        id=2,
        role=SimpleNamespace(value="LEADER"),
        leader_person_id=root_id,
        leader_person=None,
    )


def measure(label: str, fn, repeats: int = 3) -> None:
    timings: list[float] = []
    result = None
    for _ in range(repeats):
        started = time.perf_counter()
        result = fn()
        timings.append((time.perf_counter() - started) * 1000)
    summary = ""
    if isinstance(result, tuple) and len(result) == 2:
        summary = f" (нийт {result[1]:,})"
    elif isinstance(result, list):
        summary = f" ({len(result)} мөр)"
    print(f"  {label:<46} {min(timings):8.1f} ms{summary}")


def run_benchmarks(engine) -> None:
    admin = admin_user()
    scoped = scoped_user()

    with engine.connect() as conn:
        print("\nSQL benchmark:")
        measure(
            "COUNT идэвхтэй бүртгэл",
            lambda: conn.execute(
                text("SELECT count(*) FROM people WHERE status = 'ACTIVE'")
            ).scalar_one(),
        )
        measure(
            "Регистрээр яг таарах",
            lambda: conn.execute(
                text("SELECT id FROM people WHERE reg_number = :reg"),
                {"reg": "БН00012345"},
            ).first(),
        )
        measure(
            "FTS: овгоор (Бат)",
            lambda: conn.execute(
                text(
                    "SELECT count(*) FROM people WHERE "
                    "to_tsvector('simple', last_name) @@ to_tsquery('simple', 'Бат:*')"
                )
            ).scalar_one(),
        )
        measure(
            "Дүүрэг prefix (Хан-Уул)",
            lambda: conn.execute(
                text("SELECT count(*) FROM people WHERE lower(district) LIKE 'хан-уул%'")
            ).scalar_one(),
        )

    from app.core.database import SessionLocal

    with SessionLocal() as db:
        print("\nRepository / service benchmark:")
        measure(
            "Жагсаалт, админ, 1-р хуудас",
            lambda: people_repo.search_people(
                db, admin, page=1, page_size=20, status=PersonStatus.ACTIVE
            ),
        )
        measure(
            "Жагсаалт, scope root=1, 1-р хуудас",
            lambda: people_repo.search_people(
                db, scoped, page=1, page_size=20, status=PersonStatus.ACTIVE
            ),
        )
        measure(
            "Хайлт: овог 'Бат' (scope root=1)",
            lambda: people_repo.search_people(
                db,
                scoped,
                page=1,
                page_size=20,
                status=PersonStatus.ACTIVE,
                last_name="Бат",
            ),
        )
        measure(
            "Хайлт: регистр (яг)",
            lambda: people_repo.search_people(
                db,
                admin,
                page=1,
                page_size=20,
                status=PersonStatus.ACTIVE,
                reg_number="БН00012345",
            ),
        )
        measure(
            "Шууд гишүүд (ARAVT #5551)",
            lambda: people_repo.direct_members(
                db, admin, 5551, page=1, page_size=100
            ),
        )
        measure(
            "Харьяаллын зам (гүн leaf)",
            lambda: people_repo.path_to_person(db, admin, TOTAL),
        )
        measure(
            "Closure descendant count root=1",
            lambda: db.execute(
                text(
                    "SELECT count(*) FROM person_closure WHERE ancestor_id = 1"
                )
            ).scalar_one(),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Дахин үүсгэх")
    args = parser.parse_args()

    url = settings.database_url
    if "bench" not in url:
        raise SystemExit(
            "Аюулгүй байдлын үүднээс зөвхөн нэрэндээ 'bench' агуулсан database дээр ажиллана."
        )

    engine = create_engine(url, future=True)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM people")).scalar_one()
    if args.force or count < TOTAL:
        print(f"Өгөгдөл үүсгэж байна ({count:,} → {TOTAL:,})…")
        with engine.begin() as conn:
            seed(conn)
    else:
        print(f"Одоо байгаа өгөгдлийг ашиглана: {count:,} бүртгэл.")

    run_benchmarks(engine)
    engine.dispose()


if __name__ == "__main__":
    main()
