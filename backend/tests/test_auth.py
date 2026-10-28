from tests.conftest import auth_headers, create_user, login


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_login_sets_cookies_and_me(client):
    create_user(username="bat", full_name="Бат")
    csrf = login(client, "bat")
    assert csrf
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    body = me.json()
    assert body["user"]["username"] == "bat"
    assert body["user"]["permissions"]["can_edit"] is False
    assert body["csrf_token"] == csrf
    assert client.cookies.get("pr_session")
    assert client.cookies.get("pr_csrf")


def test_login_wrong_password(client):
    create_user(username="bat")
    response = client.post("/api/auth/login", json={"username": "bat", "password": "WrongPass123"})
    assert response.status_code == 401
    assert "pr_session" not in client.cookies


def test_inactive_user_cannot_login(client):
    create_user(username="bat", is_active=False)
    response = client.post("/api/auth/login", json={"username": "bat", "password": "Password1234"})
    assert response.status_code == 401


def test_username_is_normalized(client):
    create_user(username="bat")
    csrf = login(client, "  BAT  ")
    assert csrf


def test_requires_authentication(client):
    assert client.get("/api/people").status_code == 401
    assert client.get("/api/dashboard").status_code == 401


def test_mutation_requires_csrf(admin_auth):
    client = admin_auth["client"]
    response = client.post("/api/people", json={})
    assert response.status_code == 403
    assert response.json()["code"] == "CSRF_FAILED"


def test_logout_revokes_session(client):
    create_user(username="bat")
    csrf = login(client, "bat")
    response = client.post("/api/auth/logout", headers=auth_headers(csrf))
    assert response.status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_change_password(client):
    create_user(username="bat")
    csrf = login(client, "bat")
    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "Password1234", "new_password": "NewPassword5678"},
        headers=auth_headers(csrf),
    )
    assert response.status_code == 200
    assert client.post("/api/auth/logout", headers=auth_headers(csrf)).status_code == 200
    assert (
        client.post("/api/auth/login", json={"username": "bat", "password": "Password1234"}).status_code
        == 401
    )
    login(client, "bat", "NewPassword5678")


def test_change_password_wrong_current(client):
    create_user(username="bat")
    csrf = login(client, "bat")
    response = client.post(
        "/api/auth/change-password",
        json={"current_password": "Wrong12345", "new_password": "NewPassword5678"},
        headers=auth_headers(csrf),
    )
    assert response.status_code == 403


def test_login_rate_limit(client):
    create_user(username="ratelimited")
    for _ in range(10):
        client.post(
            "/api/auth/login",
            json={"username": "ratelimited", "password": "WrongPass123"},
        )
    response = client.post(
        "/api/auth/login",
        json={"username": "ratelimited", "password": "WrongPass123"},
    )
    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMITED"
