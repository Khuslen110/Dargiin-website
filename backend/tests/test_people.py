from tests.conftest import (
    auth_headers,
    create_person,
    login,
    person_payload,
)


def _create_scoped_user(admin_auth, root_id: int, *, username: str = "scoped", **overrides):
    payload = {
        "username": username,
        "full_name": "Харьяаллын хэрэглэгч",
        "password": "Password1234",
        "role": "LEADER",
        "leader_person_id": root_id,
    }
    payload.update(overrides)
    response = admin_auth["client"].post("/api/users", json=payload, headers=auth_headers(admin_auth["csrf"]))
    assert response.status_code == 201, response.text
    return response.json()


def _login_scoped(client, username="scoped"):
    csrf = login(client, username)
    return csrf


def test_create_and_normalize_reg_number(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    person = create_person(
        client,
        csrf,
        reg_number="тб 0000-0001",
        phone="+976 9911-2233",
    )
    assert person["reg_number"] == "ТБ00000001"
    assert person["phone"] == "+97699112233"
    assert person["age"] == 36

    duplicate = client.post(
        "/api/people",
        json=person_payload(reg_number="ТБ00000001"),
        headers=auth_headers(csrf),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "DUPLICATE_REG_NUMBER"


def test_invalid_registration_and_birth_date(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    bad_reg = client.post(
        "/api/people",
        json=person_payload(reg_number="AB123"),
        headers=auth_headers(csrf),
    )
    assert bad_reg.status_code == 422
    assert "reg_number" in bad_reg.json()["fields"]

    future = client.post(
        "/api/people",
        json=person_payload(birth_date="2999-01-01"),
        headers=auth_headers(csrf),
    )
    assert future.status_code == 422
    assert "birth_date" in future.json()["fields"]


def test_search_filters_and_pagination(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(client, csrf, last_name="Батбаяр", first_name="Сүхбат")
    myangat = create_person(
        client, csrf, last_name="Дорж", first_name="Бат", group_type="MYANGAT", parent_id=root["id"]
    )
    create_person(
        client, csrf, last_name="Эрдэнэ", first_name="Оюун", group_type="ZUUT", parent_id=myangat["id"]
    )

    by_name = client.get("/api/people", params={"last_name": "Бат"})
    assert by_name.status_code == 200
    assert by_name.json()["total"] == 1
    assert by_name.json()["items"][0]["id"] == root["id"]

    by_reg = client.get("/api/people", params={"reg_number": root["reg_number"].lower()})
    assert by_reg.json()["total"] == 1

    by_group = client.get("/api/people", params={"group_type": "ZUUT"})
    assert by_group.json()["total"] == 1

    paged = client.get("/api/people", params={"page_size": 2, "sort": "last_name", "order": "asc"})
    body = paged.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["total_pages"] == 2

    invalid_sort = client.get("/api/people", params={"sort": "phone;drop"})
    assert invalid_sort.status_code == 422


def test_scope_and_sensitive_access(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(client, csrf)
    own = create_person(
        client, csrf, group_type="MYANGAT", parent_id=root["id"]
    )
    other = create_person(client, csrf)
    _create_scoped_user(admin_auth, own["id"])
    _login_scoped(client)

    listing = client.get("/api/people").json()
    assert listing["total"] == 3
    by_id = {item["id"]: item for item in listing["items"]}
    assert by_id[own["id"]]["full_profile"] is True
    assert by_id[root["id"]]["full_profile"] is False
    assert by_id[other["id"]]["full_profile"] is False
    assert by_id[root["id"]]["phone"] == "99112233"

    detail = client.get(f"/api/people/{own['id']}")
    assert detail.status_code == 200
    assert detail.json()["address"] == "2-р байр 101"
    assert detail.json()["permissions"]["can_view_sensitive"] is True
    assert detail.json()["permissions"]["can_view_full"] is True

    limited = client.get(f"/api/people/{other['id']}").json()
    assert limited["full_profile"] is False
    assert limited["phone"] == other["phone"]
    assert limited["address"] == other["address"]
    assert limited["job"] is None
    assert limited["permissions"]["can_view_full"] is False

    assert client.get("/api/dashboard").json()["total_people"] == 1


def test_leader_can_only_add_direct_child(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(client, csrf)
    outside = create_person(client, csrf)
    _create_scoped_user(admin_auth, root["id"])
    user_csrf = _login_scoped(client)

    child = create_person(client, user_csrf, parent_id=None, group_type="MYANGAT")
    assert child["parent_id"] == root["id"]

    forged_parent = client.post(
        "/api/people",
        json=person_payload(parent_id=outside["id"], group_type="MYANGAT"),
        headers=auth_headers(user_csrf),
    )
    assert forged_parent.status_code == 400

    wrong_type = client.post(
        "/api/people",
        json=person_payload(parent_id=root["id"], group_type="ZUUT"),
        headers=auth_headers(user_csrf),
    )
    assert wrong_type.status_code == 400

    grandchild = client.post(
        "/api/people",
        json=person_payload(parent_id=child["id"], group_type="ZUUT"),
        headers=auth_headers(user_csrf),
    )
    assert grandchild.status_code == 400
    assert client.get("/api/people").json()["total"] == 3
    assert client.get(f"/api/people/{child['id']}").status_code == 200


def test_leader_cannot_edit_outside_scope(admin_auth):
    client = admin_auth["client"]
    root = create_person(client, admin_auth["csrf"])
    outside = create_person(client, admin_auth["csrf"])
    _create_scoped_user(admin_auth, root["id"])
    user_csrf = _login_scoped(client)
    response = client.patch(
        f"/api/people/{outside['id']}",
        json={"job": "Багш"},
        headers=auth_headers(user_csrf),
    )
    assert response.status_code == 403


def test_user_can_update_visible_person(admin_auth):
    client = admin_auth["client"]
    root = create_person(client, admin_auth["csrf"])
    _create_scoped_user(admin_auth, root["id"])
    user_csrf = _login_scoped(client)

    response = client.patch(
        f"/api/people/{root['id']}",
        json={"job": "Багш", "phone": None},
        headers=auth_headers(user_csrf),
    )
    assert response.status_code == 200
    assert response.json()["job"] == "Багш"
    assert response.json()["phone"] is None


def test_leader_can_edit_own_record(admin_auth):
    client = admin_auth["client"]
    root = create_person(client, admin_auth["csrf"])
    _create_scoped_user(admin_auth, root["id"], username="editor")
    user_csrf = _login_scoped(client, "editor")
    response = client.patch(
        f"/api/people/{root['id']}",
        json={"job": "Багш"},
        headers=auth_headers(user_csrf),
    )
    assert response.status_code == 200
    assert response.json()["job"] == "Багш"


def test_soft_delete_restore_and_purge_rules(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    parent = create_person(client, csrf)
    child = create_person(client, csrf, parent_id=parent["id"], group_type="MYANGAT")

    _create_scoped_user(admin_auth, parent["id"], username="scoped2")
    user_csrf = _login_scoped(client, "scoped2")
    forbidden_delete = client.delete(f"/api/people/{child['id']}", headers=auth_headers(user_csrf))
    assert forbidden_delete.status_code == 403

    # Admin session: log in again in a fresh client is not needed; admin cookie was replaced
    # by the scoped user login above. Use a separate client.
    from fastapi.testclient import TestClient

    from app.main import app

    admin_client = TestClient(app)
    admin_csrf = login(admin_client, "admin")

    deleted = admin_client.delete(f"/api/people/{child['id']}", headers=auth_headers(admin_csrf))
    assert deleted.status_code == 200
    assert admin_client.get(f"/api/people/{child['id']}").status_code == 200

    active_list = admin_client.get("/api/people").json()
    assert active_list["total"] == 1
    deleted_list = admin_client.get("/api/people", params={"status": "DELETED"}).json()
    assert deleted_list["total"] == 1

    restored = admin_client.post(f"/api/people/{child['id']}/restore", headers=auth_headers(admin_csrf))
    assert restored.status_code == 200
    assert restored.json()["status"] == "ACTIVE"

    admin_client.delete(f"/api/people/{child['id']}", headers=auth_headers(admin_csrf))
    bad_confirm = admin_client.post(
        f"/api/people/{child['id']}/purge",
        json={"confirm_reg_number": "ТБ99999999"},
        headers=auth_headers(admin_csrf),
    )
    assert bad_confirm.status_code == 400

    purged = admin_client.post(
        f"/api/people/{child['id']}/purge",
        json={"confirm_reg_number": child["reg_number"]},
        headers=auth_headers(admin_csrf),
    )
    assert purged.status_code == 200
    assert admin_client.get(f"/api/people/{child['id']}").status_code == 404

    admin_client.delete(f"/api/people/{parent['id']}", headers=auth_headers(admin_csrf))


def test_purge_blocked_when_children_exist(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    parent = create_person(client, csrf)
    create_person(client, csrf, parent_id=parent["id"], group_type="MYANGAT")
    client.delete(f"/api/people/{parent['id']}", headers=auth_headers(csrf))
    response = client.post(
        f"/api/people/{parent['id']}/purge",
        json={"confirm_reg_number": parent["reg_number"]},
        headers=auth_headers(csrf),
    )
    assert response.status_code == 409


def test_person_history_and_permissions(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    person = create_person(client, csrf)
    client.patch(
        f"/api/people/{person['id']}",
        json={"job": "Эмч"},
        headers=auth_headers(csrf),
    )
    history = client.get(f"/api/people/{person['id']}/history")
    assert history.status_code == 200
    actions = [item["action"] for item in history.json()]
    assert "PERSON_CREATE" in actions
    assert "PERSON_UPDATE" in actions
    update_entry = next(item for item in history.json() if item["action"] == "PERSON_UPDATE")
    assert "job" in update_entry["metadata"]["changed"]


def test_phone_search_is_scoped(admin_auth):
    client = admin_auth["client"]
    root = create_person(client, admin_auth["csrf"])
    create_person(client, admin_auth["csrf"], phone="88112233")
    _create_scoped_user(admin_auth, root["id"], username="scoped3")
    user_csrf = _login_scoped(client, "scoped3")
    response = client.get("/api/people", params={"phone": "9911"})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [root["id"]]
    assert user_csrf
