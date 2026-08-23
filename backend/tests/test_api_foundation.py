def test_not_found_returns_envelope(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["message"]
    assert body["errors"] == []


def test_validation_error_returns_envelope(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "not-an-email", "password": ""},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Validation failed"
    assert len(body["errors"]) > 0


def test_cors_allows_frontend_origin(client):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_auth_unauthorized_returns_envelope(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Authentication required"
    assert body["errors"] == []
