from tests.conftest import auth_headers, create_person
from tests.test_people import _create_scoped_user, _login_scoped


def _tree(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    a = create_person(client, csrf, last_name="А", first_name="Түмт", group_type="TUMT")
    b = create_person(
        client, csrf, last_name="Б", first_name="Мянгат", group_type="MYANGAT", parent_id=a["id"]
    )
    c = create_person(
        client, csrf, last_name="В", first_name="Мянгат 2", group_type="MYANGAT", parent_id=a["id"]
    )
    d = create_person(client, csrf, last_name="Г", first_name="Зуут", group_type="ZUUT", parent_id=b["id"])
    return a, b, c, d


def test_direct_members_are_not_inherited(admin_auth):
    client = admin_auth["client"]
    a, b, c, d = _tree(admin_auth)

    a_detail = client.get(f"/api/people/{a['id']}").json()
    assert a_detail["direct_member_count"] == 2
    assert a_detail["permissions"]["can_edit"] is True

    a_members = client.get(f"/api/people/{a['id']}/members").json()
    ids = {item["id"] for item in a_members["items"]}
    assert ids == {b["id"], c["id"]}
    assert d["id"] not in ids

    b_members = client.get(f"/api/people/{b['id']}/members").json()
    assert {item["id"] for item in b_members["items"]} == {d["id"]}

    d_detail = client.get(f"/api/people/{d['id']}").json()
    assert [item["id"] for item in d_detail["path"]] == [a["id"], b["id"]]
    assert d_detail["path"][-1]["id"] == b["id"]
    assert d_detail["parent"]["id"] == b["id"]
    assert c["id"] != b["id"]


def test_scope_subtree_and_path(admin_auth):
    client = admin_auth["client"]
    a, b, c, d = _tree(admin_auth)
    _create_scoped_user(admin_auth, b["id"], username="scopedb")
    _login_scoped(client, "scopedb")

    listing = client.get("/api/people").json()
    assert {item["id"] for item in listing["items"]} == {a["id"], b["id"], c["id"], d["id"]}
    full_ids = {item["id"] for item in listing["items"] if item["full_profile"]}
    assert full_ids == {b["id"], d["id"]}

    detail = client.get(f"/api/people/{d['id']}").json()
    assert [item["id"] for item in detail["path"]] == [b["id"]]

    limited = client.get(f"/api/people/{a['id']}").json()
    assert limited["full_profile"] is False
    assert limited["job"] is None
    assert limited["parent"] is None
    assert limited["path"] == []
    assert limited["phone"] == a["phone"]
    assert limited["address"] == a["address"]
    assert limited["permissions"]["can_view_full"] is False

    other_limited = client.get(f"/api/people/{c['id']}").json()
    assert other_limited["full_profile"] is False
    assert other_limited["job"] is None

    roots = client.get("/api/hierarchy/roots").json()
    assert [root["id"] for root in roots] == [b["id"]]
    assert roots[0]["direct_member_count"] == 1


def test_circular_relationship_prevented(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    a, b, _c, d = _tree(admin_auth)
    response = client.patch(
        f"/api/people/{a['id']}",
        json={"parent_id": d["id"]},
        headers=auth_headers(csrf),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "CIRCULAR_HIERARCHY"

    self_parent = client.patch(
        f"/api/people/{b['id']}",
        json={"parent_id": b["id"]},
        headers=auth_headers(csrf),
    )
    assert self_parent.status_code == 400


def test_move_subtree_updates_closure(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    a, b, _c, d = _tree(admin_auth)

    moved = client.patch(
        f"/api/people/{d['id']}",
        json={"parent_id": _c["id"]},
        headers=auth_headers(csrf),
    )
    assert moved.status_code == 200
    assert moved.json()["parent"]["id"] == _c["id"]
    assert [item["id"] for item in moved.json()["path"]] == [a["id"], _c["id"]]

    a_members = client.get(f"/api/people/{a['id']}/members").json()
    assert {item["id"] for item in a_members["items"]} == {b["id"], _c["id"]}
    b_members = client.get(f"/api/people/{b['id']}/members").json()
    assert b_members["total"] == 0
    c_members = client.get(f"/api/people/{_c['id']}/members").json()
    assert {item["id"] for item in c_members["items"]} == {d["id"]}

    _create_scoped_user(admin_auth, b["id"], username="scopedb2")
    _login_scoped(client, "scopedb2")
    moved_out_of_scope = client.get(f"/api/people/{d['id']}").json()
    assert moved_out_of_scope["full_profile"] is False
    assert moved_out_of_scope["job"] is None
    assert moved_out_of_scope["parent"] is None


def test_deleted_parent_does_not_cascade(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    _a, b, _c, d = _tree(admin_auth)
    client.delete(f"/api/people/{b['id']}", headers=auth_headers(csrf))

    # Хүүхэд идэвхтэй хэвээр, audit/closure хөндөгдөхгүй
    detail = client.get(f"/api/people/{d['id']}")
    assert detail.status_code == 200
    assert detail.json()["parent"]["status"] == "DELETED"

    restored = client.post(f"/api/people/{b['id']}/restore", headers=auth_headers(csrf))
    assert restored.status_code == 200
    assert restored.json()["direct_member_count"] == 1


def test_parent_candidates_are_scope_limited(admin_auth):
    client = admin_auth["client"]
    a, b, _c, _d = _tree(admin_auth)
    _create_scoped_user(admin_auth, b["id"], username="scopedb3")
    csrf = _login_scoped(client, "scopedb3")
    response = client.get("/api/people/parent-candidates", params={"search": "Мян"})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert a["id"] not in ids
    assert b["id"] in ids
    assert csrf
