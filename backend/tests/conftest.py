import itertools
import os

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/people_registry_test",
)
os.environ["COOKIE_SECURE"] = "false"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import Role  # noqa: E402
from app.models.user import User  # noqa: E402

_reg_counter = itertools.count(1)


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables(_prepare_database):
    table_names = ", ".join(table.name for table in Base.metadata.tables.values())
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_user(
    *,
    username: str,
    password: str = "Password1234",
    role: Role = Role.LEADER,
    is_active: bool = True,
    leader_person_id: int | None = None,
    full_name: str | None = None,
) -> int:
    with SessionLocal() as session:
        user = User(
            username=username,
            full_name=full_name or f"Тест {username}",
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
            leader_person_id=leader_person_id,
        )
        session.add(user)
        session.commit()
        return user.id


def login(client: TestClient, username: str, password: str = "Password1234") -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


def next_reg_number() -> str:
    return f"ТБ{next(_reg_counter):08d}"


def person_payload(**overrides):
    data = {
        "reg_number": next_reg_number(),
        "last_name": "Батбаяр",
        "first_name": "Сүхбат",
        "gender": "MALE",
        "birth_date": "1990-05-12",
        "phone": "99112233",
        "district": "Хан-Уул",
        "khoroo": "1-р хороо",
        "address": "2-р байр 101",
        "job": "Инженер",
        "group_type": "TUMT",
        "parent_id": None,
    }
    data.update(overrides)
    return data


def create_person(client: TestClient, csrf: str, *, expected_status: int = 201, **overrides) -> dict:
    response = client.post(
        "/api/people",
        json=person_payload(**overrides),
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == expected_status, response.text
    return response.json()


@pytest.fixture
def admin_auth(client):
    create_user(username="admin", role=Role.ADMIN, full_name="Админ")
    csrf = login(client, "admin")
    return {"client": client, "csrf": csrf}


def auth_headers(csrf: str) -> dict[str, str]:
    return {"X-CSRF-Token": csrf}
