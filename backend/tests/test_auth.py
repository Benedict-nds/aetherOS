DEMO_EMAIL = "admin@aetherqore.local"
DEMO_PASSWORD = "Admin123!"


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["user"]["email"] == DEMO_EMAIL
    assert "password_hash" not in body["data"]["user"]


def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": DEMO_EMAIL,
            "password": "WrongPassword!",
        },
    )

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Invalid credentials"


def test_me_missing_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_with_valid_token(client):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
        },
    )
    token = login_response.json()["data"]["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == DEMO_EMAIL
    assert "password_hash" not in body["data"]


def test_logout_with_valid_token(client):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
        },
    )
    token = login_response.json()["data"]["access_token"]

    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
