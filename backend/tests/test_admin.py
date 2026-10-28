from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import auth_headers, create_person, create_user, login


def _user_payload(root_id: int | None = None, **overrides):
    payload = {
        "username": "manager",
        "full_name": "Удирдагч хэрэглэгч",
        "password": "Password1234",
        "role": "LEADER",
        "leader_person_id": root_id,
    }
    payload.update(overrides)
    return payload


def test_admin_can_create_list_and_update_user(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(client, csrf)
    response = client.post("/api/users", json=_user_payload(root["id"]), headers=auth_headers(csrf))
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["role"] == "LEADER"
    assert created["leader_person"]["id"] == root["id"]

    listing = client.get("/api/users").json()
    assert listing["total"] == 2
    usernames = {item["username"] for item in listing["items"]}
    assert usernames == {"admin", "manager"}

    updated = client.patch(
        f"/api/users/{created['id']}",
        json={"full_name": "Шинэ нэр"},
        headers=auth_headers(csrf),
    )
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Шинэ нэр"


def test_leader_requires_valid_leader_person(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    no_leader = client.post("/api/users", json=_user_payload(), headers=auth_headers(csrf))
    assert no_leader.status_code == 400

    missing_leader = client.post(
        "/api/users",
        json=_user_payload(999999),
        headers=auth_headers(csrf),
    )
    assert missing_leader.status_code == 400


def test_regular_user_cannot_manage_users(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(client, csrf)
    client.post("/api/users", json=_user_payload(root["id"]), headers=auth_headers(csrf))
    user_client = TestClient(app)
    login(user_client, "manager")
    assert user_client.get("/api/users").status_code == 403
    assert user_client.get("/api/audit").status_code == 403


def test_cannot_change_own_privileges(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    me = client.get("/api/auth/me").json()["user"]
    response = client.patch(
        f"/api/users/{me['id']}",
        json={"role": "LEADER", "leader_person_id": None},
        headers=auth_headers(csrf),
    )
    assert response.status_code == 403

    full_name_only = client.patch(
        f"/api/users/{me['id']}",
        json={"full_name": "Шинэ админ нэр"},
        headers=auth_headers(csrf),
    )
    assert full_name_only.status_code == 200


def test_admin_reset_password_revokes_sessions(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(client, csrf)
    created = client.post("/api/users", json=_user_payload(root["id"]), headers=auth_headers(csrf)).json()
    user_client = TestClient(app)
    login(user_client, "manager")
    assert user_client.get("/api/auth/me").status_code == 200

    reset = client.post(
        f"/api/users/{created['id']}/reset-password",
        json={"new_password": "AnotherPass987"},
        headers=auth_headers(csrf),
    )
    assert reset.status_code == 200
    assert user_client.get("/api/auth/me").status_code == 401
    login(user_client, "manager", "AnotherPass987")


def test_disabling_user_revokes_access(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(client, csrf)
    created = client.post("/api/users", json=_user_payload(root["id"]), headers=auth_headers(csrf)).json()
    user_client = TestClient(app)
    login(user_client, "manager")
    response = client.patch(
        f"/api/users/{created['id']}",
        json={"is_active": False},
        headers=auth_headers(csrf),
    )
    assert response.status_code == 200
    assert user_client.get("/api/auth/me").status_code == 401
    assert (
        user_client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "Password1234"},
        ).status_code
        == 401
    )


def test_audit_is_admin_only_and_records_actions(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(client, csrf)
    client.patch(
        f"/api/people/{root['id']}",
        json={"job": "Багш"},
        headers=auth_headers(csrf),
    )
    audit = client.get("/api/audit", params={"page_size": 50})
    assert audit.status_code == 200
    assert audit.json()["total"] >= 2
    actions = [item["action"] for item in audit.json()["items"]]
    assert "PERSON_CREATE" in actions
    assert "PERSON_UPDATE" in actions
    assert "AUTH_LOGIN_SUCCESS" in actions
    for item in audit.json()["items"]:
        assert "password" not in str(item["metadata"]).lower()

    filtered = client.get("/api/audit", params={"action": "PERSON_CREATE"}).json()
    assert filtered["total"] == 1


def test_duplicate_username_rejected(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    create_user(username="existing")
    root = create_person(client, csrf)
    response = client.post(
        "/api/users",
        json=_user_payload(root["id"], username="Existing"),
        headers=auth_headers(csrf),
    )
    assert response.status_code == 409
