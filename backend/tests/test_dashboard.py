from app.core.config import settings


def _auth_headers(client) -> dict[str, str]:
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": settings.demo_email,
            "password": settings.demo_password,
        },
    )
    token = login_response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_summary_requires_auth(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Authentication required"


def test_dashboard_summary_returns_expected_shape(client):
    response = client.get(
        "/api/dashboard/summary",
        headers=_auth_headers(client),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Dashboard summary retrieved"

    data = body["data"]
    assert data["today_sales"] == {"amount": 0, "currency": "GHS"}
    assert data["low_stock_count"] == 0
    assert data["expiring_soon_count"] == 0
    assert data["open_orders_count"] == 0
