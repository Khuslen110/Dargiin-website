from tests.conftest import create_person
from tests.test_people import _create_scoped_user, _login_scoped


def test_dashboard_distribution_stats(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(
        client,
        csrf,
        last_name="Бат",
        first_name="Эр",
        gender="MALE",
        birth_date="1990-01-01",
        district="Хан-Уул",
        khoroo="1-р хороо",
    )
    create_person(
        client,
        csrf,
        last_name="Дорж",
        first_name="Эм",
        gender="FEMALE",
        birth_date="2010-01-01",
        district="Баянзүрх",
        khoroo="5-р хороо",
        group_type="MYANGAT",
        parent_id=root["id"],
    )

    data = client.get("/api/dashboard").json()
    assert data["total_people"] == 2
    assert {item["gender"]: item["count"] for item in data["gender_counts"]} == {
        "MALE": 1,
        "FEMALE": 1,
        "OTHER": 0,
    }
    assert {item["label"]: item["count"] for item in data["age_counts"]}["35–44"] == 1
    assert {item["label"]: item["count"] for item in data["age_counts"]}["0–17"] == 1
    assert {item["name"]: item["count"] for item in data["district_counts"]} == {
        "Хан-Уул": 1,
        "Баянзүрх": 1,
    }
    assert {item["name"]: item["count"] for item in data["khoroo_counts"]} == {
        "1-р хороо": 1,
        "5-р хороо": 1,
    }
    assert len(data["daily_registrations"]) == 7
    assert sum(item["count"] for item in data["daily_registrations"]) == 2
    assert {item["group_type"] for item in data["group_counts"]} == {
        "TUMT", "MYANGAT", "ZUUT", "ARAVT", "MEMBER"
    }
    assert data["group_counts"][0]["count"] == 1
    assert data["group_counts"][1]["count"] == 1


def test_dashboard_distribution_respects_scope(admin_auth):
    client, csrf = admin_auth["client"], admin_auth["csrf"]
    root = create_person(
        client, csrf, gender="MALE", district="Хан-Уул", khoroo="1-р хороо"
    )
    myangat = create_person(
        client,
        csrf,
        gender="FEMALE",
        district="Хан-Уул",
        khoroo="1-р хороо",
        group_type="MYANGAT",
        parent_id=root["id"],
    )
    create_person(
        client,
        csrf,
        gender="MALE",
        district="Хан-Уул",
        khoroo="1-р хороо",
        group_type="ZUUT",
        parent_id=myangat["id"],
    )
    create_person(
        client, csrf, gender="FEMALE", district="Сүхбаатар", khoroo="9-р хороо"
    )

    _create_scoped_user(admin_auth, myangat["id"])
    _login_scoped(client)
    data = client.get("/api/dashboard").json()

    assert data["total_people"] == 2
    assert {item["gender"]: item["count"] for item in data["gender_counts"]}["FEMALE"] == 1
    assert {item["name"]: item["count"] for item in data["district_counts"]} == {
        "Хан-Уул": 2
    }
    assert {item["name"]: item["count"] for item in data["khoroo_counts"]} == {
        "1-р хороо": 2
    }
