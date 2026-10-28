from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import Role
from tests.conftest import auth_headers, create_person, create_user, login


def _create_chain(client, csrf):
    root = create_person(client, csrf, group_type="TUMT")
    child = create_person(
        client,
        csrf,
        group_type="MYANGAT",
        parent_id=root["id"],
        first_name="Хүү",
    )
    grandchild = create_person(
        client,
        csrf,
        group_type="ZUUT",
        parent_id=child["id"],
        first_name="Ач",
    )
    aravt = create_person(
        client,
        csrf,
        group_type="ARAVT",
        parent_id=grandchild["id"],
        first_name="Аравт",
    )
    member = create_person(
        client,
        csrf,
        group_type="MEMBER",
        parent_id=aravt["id"],
        first_name="Гишүүн",
    )
    return root, child, grandchild, aravt, member


def test_direct_parent_can_create_and_reset_child_account(admin_auth):
    client, admin_csrf = admin_auth["client"], admin_auth["csrf"]
    root, child, grandchild, aravt, member = _create_chain(client, admin_csrf)
    create_user(
        username="root.leader",
        role=Role.LEADER,
        leader_person_id=root["id"],
        full_name="Түмтийн удирдагч",
    )
    csrf = login(client, "root.leader")

    child_detail = client.get(f"/api/people/{child['id']}").json()
    assert child_detail["permissions"]["can_manage_account"] is True
    assert client.get(f"/api/people/{grandchild['id']}").json()["permissions"]["can_manage_account"] is False
    assert client.get(f"/api/people/{root['id']}").json()["permissions"]["can_manage_account"] is False

    state = client.get(f"/api/people/{child['id']}/account")
    assert state.status_code == 200
    assert state.json()["account"] is None

    created = client.post(
        f"/api/people/{child['id']}/account",
        json={"username": "child.leader", "password": "ChildPass2026"},
        headers=auth_headers(csrf),
    )
    assert created.status_code == 201, created.text
    assert created.json()["username"] == "child.leader"
    assert created.json()["role"] == "LEADER"

    duplicate = client.post(
        f"/api/people/{child['id']}/account",
        json={"username": "another.leader", "password": "ChildPass2026"},
        headers=auth_headers(csrf),
    )
    assert duplicate.status_code == 409

    assert client.get(f"/api/people/{grandchild['id']}/account").status_code == 403
    assert (
        client.post(
            f"/api/people/{grandchild['id']}/account",
            json={"username": "grand.leader", "password": "ChildPass2026"},
            headers=auth_headers(csrf),
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/people/{root['id']}/account",
            json={"username": "self.leader", "password": "ChildPass2026"},
            headers=auth_headers(csrf),
        ).status_code
        == 403
    )

    old_session = TestClient(app)
    login(old_session, "child.leader", "ChildPass2026")
    reset = client.post(
        f"/api/people/{child['id']}/account/reset-password",
        json={"new_password": "NewChildPass2026"},
        headers=auth_headers(csrf),
    )
    assert reset.status_code == 200, reset.text
    assert old_session.get("/api/auth/me").status_code == 401
    assert (
        old_session.post(
            "/api/auth/login",
            json={"username": "child.leader", "password": "ChildPass2026"},
        ).status_code
        == 401
    )
    login(old_session, "child.leader", "NewChildPass2026")


def test_aravt_creates_member_account_and_admin_fallback(admin_auth):
    client, admin_csrf = admin_auth["client"], admin_auth["csrf"]
    _root, _child, _grandchild, aravt, member = _create_chain(client, admin_csrf)
    create_user(
        username="aravt.leader",
        role=Role.LEADER,
        leader_person_id=aravt["id"],
        full_name="Аравтын удирдагч",
    )
    csrf = login(client, "aravt.leader")

    created = client.post(
        f"/api/people/{member['id']}/account",
        json={"username": "member.login", "password": "MemberPass2026"},
        headers=auth_headers(csrf),
    )
    assert created.status_code == 201, created.text
    assert created.json()["role"] == "MEMBER"

    member_client = TestClient(app)
    login(member_client, "member.login", "MemberPass2026")
    assert member_client.get("/api/auth/me").json()["user"]["role"] == "MEMBER"
    member_detail = member_client.get(f"/api/people/{member['id']}").json()
    assert member_detail["permissions"]["can_manage_account"] is False

    login(client, "admin")
    admin_view = client.get(f"/api/people/{member['id']}/account")
    assert admin_view.status_code == 200
    assert admin_view.json()["account"]["username"] == "member.login"
    assert client.get(f"/api/people/{aravt['id']}").json()["permissions"]["can_manage_account"] is True
