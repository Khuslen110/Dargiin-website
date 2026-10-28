from app.models.enums import Role
from tests.conftest import auth_headers, create_person, create_user, person_payload
from tests.test_people import _create_scoped_user, _login_scoped


def _chain(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    tumt = create_person(client, csrf, last_name="А", first_name="Түмт", group_type="TUMT")
    myangat = create_person(
        client, csrf, last_name="Б", first_name="Мянгат", group_type="MYANGAT", parent_id=tumt["id"]
    )
    zuut = create_person(
        client, csrf, last_name="В", first_name="Зуут", group_type="ZUUT", parent_id=myangat["id"]
    )
    aravt = create_person(
        client, csrf, last_name="Г", first_name="Аравт", group_type="ARAVT", parent_id=zuut["id"]
    )
    member = create_person(
        client, csrf, last_name="Д", first_name="Гишүүн", group_type="MEMBER", parent_id=aravt["id"]
    )
    return tumt, myangat, zuut, aravt, member


def test_admin_hierarchy_must_follow_exact_levels(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    tumt, myangat, zuut, aravt, member = _chain(admin_auth)

    root_must_be_tumt = client.post(
        "/api/people", json={
            **person_payload(group_type="MYANGAT", parent_id=None)
        }, headers=auth_headers(csrf),
    )
    assert root_must_be_tumt.status_code == 400

    tumt_with_parent = client.post(
        "/api/people", json={
            **person_payload(group_type="TUMT", parent_id=tumt["id"])
        }, headers=auth_headers(csrf),
    )
    assert tumt_with_parent.status_code == 400

    skipped = client.post(
        "/api/people", json={
            **person_payload(group_type="ZUUT", parent_id=tumt["id"])
        }, headers=auth_headers(csrf),
    )
    assert skipped.status_code == 400

    member_child = client.post(
        "/api/people", json={
            **person_payload(group_type="MEMBER", parent_id=member["id"])
        }, headers=auth_headers(csrf),
    )
    assert member_child.status_code == 400
    assert [item["id"] for item in member["path"]] == [tumt["id"], myangat["id"], zuut["id"], aravt["id"]]


def test_group_change_blocked_when_children_do_not_fit(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    tumt, myangat, _zuut, _aravt, _member = _chain(admin_auth)
    second_myangat = create_person(
        client, csrf, last_name="Е", first_name="Мянгат 2", group_type="MYANGAT", parent_id=tumt["id"]
    )
    response = client.patch(
        f"/api/people/{myangat['id']}",
        json={"parent_id": second_myangat["id"], "group_type": "ZUUT"},
        headers=auth_headers(csrf),
    )
    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_GROUP_CHANGE"


def test_each_leader_adds_only_direct_next_level(admin_auth):
    client = admin_auth["client"]
    _tumt, myangat, zuut, aravt, _member = _chain(admin_auth)

    _create_scoped_user(admin_auth, myangat["id"], username="leader-my")
    _create_scoped_user(admin_auth, aravt["id"], username="leader-ar")
    my_csrf = _login_scoped(client, "leader-my")
    created_zuut = create_person(client, my_csrf, group_type="ZUUT", parent_id=None)
    assert created_zuut["parent_id"] == myangat["id"]

    wrong_level = client.post(
        "/api/people",
        json={
            **person_payload(group_type="ARAVT", parent_id=myangat["id"])
        },
        headers=auth_headers(my_csrf),
    )
    assert wrong_level.status_code == 400

    ar_csrf = _login_scoped(client, "leader-ar")
    created_member = create_person(client, ar_csrf, group_type="MEMBER", parent_id=None)
    assert created_member["parent_id"] == aravt["id"]

    under_member = client.post(
        "/api/people",
        json={
            **person_payload(group_type="MEMBER", parent_id=created_member["id"])
        },
        headers=auth_headers(ar_csrf),
    )
    assert under_member.status_code == 400

    direct_child_only = client.patch(
        f"/api/people/{zuut['id']}",
        json={"last_name": "Өөрчилсөн"},
        headers=auth_headers(ar_csrf),
    )
    assert direct_child_only.status_code in {400, 403, 404}


def test_member_cannot_be_leader_or_privileged_without_leader(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    _tumt, _myangat, _zuut, _aravt, member = _chain(admin_auth)

    payload = {
        "username": "member-leader",
        "full_name": "Гишүүн Удирдагч",
        "password": "Password1234",
        "role": "LEADER",
        "leader_person_id": member["id"],
    }
    response = client.post("/api/users", json=payload, headers=auth_headers(csrf))
    assert response.status_code == 400

    no_leader = client.post(
        "/api/users",
        json={**payload, "username": "no-leader", "leader_person_id": None},
        headers=auth_headers(csrf),
    )
    assert no_leader.status_code == 400


def test_advanced_search_and_subtree_filters(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    tumt, myangat, zuut, aravt, member = _chain(admin_auth)
    female = create_person(
        client,
        csrf,
        last_name="Баянзүрх",
        first_name="Багш",
        gender="FEMALE",
        birth_date="1970-01-01",
        address="Баянзүрх дүүрэг 5-р хороо 12-р байр",
        job="Багш",
        group_type="MYANGAT",
        parent_id=tumt["id"],
    )

    subtree = client.get(f"/api/people?under_person_id={tumt['id']}&page_size=50").json()
    assert {item["id"] for item in subtree["items"]} == {
        myangat["id"], zuut["id"], aravt["id"], member["id"], female["id"]
    }

    direct = client.get(
        f"/api/people?under_person_id={tumt['id']}&direct_only=true&page_size=50"
    ).json()
    assert {item["id"] for item in direct["items"]} == {myangat["id"], female["id"]}

    females = client.get("/api/people?gender=FEMALE").json()
    assert {item["id"] for item in females["items"]} == {female["id"]}

    by_age = client.get("/api/people?age_min=30&age_max=40&page_size=50").json()
    assert member["id"] in {item["id"] for item in by_age["items"]}
    assert female["id"] not in {item["id"] for item in by_age["items"]}

    by_address = client.get("/api/people?address=Баянзүрх").json()
    assert {item["id"] for item in by_address["items"]} == {female["id"]}

    by_job = client.get("/api/people?job=Багш").json()
    assert {item["id"] for item in by_job["items"]} == {female["id"]}

    by_group = client.get("/api/people?group_type=MEMBER").json()
    assert {item["id"] for item in by_group["items"]} == {member["id"]}

    by_reg_prefix = client.get(f"/api/people?reg_number={member['reg_number'][:5]}").json()
    assert member["id"] in {item["id"] for item in by_reg_prefix["items"]}


def test_admin_can_create_member_account(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    _tumt, _myangat, _zuut, aravt, member = _chain(admin_auth)
    sibling = create_person(
        client,
        csrf,
        last_name="Д",
        first_name="Гишүүн 2",
        group_type="MEMBER",
        parent_id=aravt["id"],
    )

    response = client.post(
        "/api/users",
        json={
            "username": "member-user",
            "full_name": "Гишүүн Хэрэглэгч",
            "password": "Password1234",
            "role": "MEMBER",
            "leader_person_id": member["id"],
        },
        headers=auth_headers(csrf),
    )
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "MEMBER"

    candidates = client.get("/api/users/member-candidates").json()
    candidate_ids = {item["id"] for item in candidates}
    assert sibling["id"] in candidate_ids
    assert member["id"] not in candidate_ids

    wrong_role = client.post(
        "/api/users",
        json={
            "username": "member-as-leader",
            "full_name": "Гишүүн Удирдагч",
            "password": "Password1234",
            "role": "LEADER",
            "leader_person_id": member["id"],
        },
        headers=auth_headers(csrf),
    )
    assert wrong_role.status_code == 400


def test_member_sees_only_same_aravt(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    _tumt, _myangat, zuut, aravt, member = _chain(admin_auth)
    sibling = create_person(
        client,
        csrf,
        last_name="Д",
        first_name="Гишүүн 2",
        group_type="MEMBER",
        parent_id=aravt["id"],
    )
    create_user(
        username="member-viewer",
        role=Role.MEMBER,
        leader_person_id=member["id"],
    )
    member_csrf = _login_scoped(client, "member-viewer")

    me = client.get("/api/auth/me").json()["user"]
    assert me["role"] == "MEMBER"
    assert me["permissions"]["can_edit"] is False
    assert me["permissions"]["can_add_child"] is False
    assert me["permissions"]["can_view_sensitive"] is True

    listing = client.get("/api/people?page_size=50").json()
    visible_ids = {item["id"] for item in listing["items"]}
    assert visible_ids == {aravt["id"], member["id"], sibling["id"]}

    own = client.get(f"/api/people/{member['id']}").json()
    assert own["full_profile"] is True

    sibling_detail = client.get(f"/api/people/{sibling['id']}").json()
    assert sibling_detail["full_profile"] is False
    assert sibling_detail["job"] is None
    assert sibling_detail["phone"] == sibling["phone"]
    assert sibling_detail["address"] == sibling["address"]

    assert client.get(f"/api/people/{zuut['id']}").status_code == 404

    forbidden = client.post(
        "/api/people",
        json={
            **person_payload(group_type="MEMBER", parent_id=aravt["id"])
        },
        headers=auth_headers(member_csrf),
    )
    assert forbidden.status_code == 403


def test_cross_tumt_view_is_full_for_tumt_and_limited_for_lower_leader(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    tumt_a = create_person(
        client, csrf, last_name="А", first_name="Түмт А", group_type="TUMT"
    )
    myangat_a = create_person(
        client,
        csrf,
        last_name="А",
        first_name="Мянгат А",
        job="Инженер А",
        group_type="MYANGAT",
        parent_id=tumt_a["id"],
    )
    tumt_x = create_person(
        client, csrf, last_name="Х", first_name="Түмт Х", group_type="TUMT"
    )
    myangat_x = create_person(
        client,
        csrf,
        last_name="Х",
        first_name="Мянгат Х",
        job="Инженер Х",
        group_type="MYANGAT",
        parent_id=tumt_x["id"],
    )

    _create_scoped_user(admin_auth, myangat_a["id"], username="cross-my")
    _create_scoped_user(admin_auth, tumt_x["id"], username="cross-tumt")
    _login_scoped(client, "cross-my")

    own = client.get(f"/api/people/{myangat_a['id']}").json()
    assert own["full_profile"] is True
    assert own["job"] == "Инженер А"

    other = client.get(f"/api/people/{myangat_x['id']}").json()
    assert other["full_profile"] is False
    assert other["job"] is None
    assert other["birth_date"] is None
    assert other["phone"] == myangat_x["phone"]
    assert other["address"] == myangat_x["address"]
    assert other["parent"] is None
    assert other["path"] == []
    assert other["permissions"]["can_view_full"] is False
    assert client.get(f"/api/people/{myangat_x['id']}/history").status_code == 404

    _login_scoped(client, "cross-tumt")

    across = client.get(f"/api/people/{myangat_a['id']}").json()
    assert across["full_profile"] is True
    assert across["job"] == "Инженер А"
    assert across["parent"]["id"] == tumt_a["id"]
