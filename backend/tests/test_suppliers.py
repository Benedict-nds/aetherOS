import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.modules.audit.service import ENTITY_TYPE_SUPPLIER


def _login(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.fixture
def owner_headers(client):
    from app.core.config import settings
    return _login(client, settings.demo_email, settings.demo_password)


@pytest.fixture
def staff_headers(client, db_session):
    role = db_session.scalar(select(Role).where(Role.name == "staff"))
    user = db_session.scalar(select(User).where(User.email == "supplier.staff@aetherqore.local"))
    if user is None:
        user = User(full_name="Supplier Staff", email="supplier.staff@aetherqore.local",
                    username="supplierstaff", password_hash=hash_password("StaffPass123!"),
                    role_id=role.id, status="active")
        db_session.add(user)
        db_session.commit()
    return _login(client, user.email, "StaffPass123!")


def test_supplier_auth_and_authorization(client, owner_headers, staff_headers):
    assert client.get("/api/suppliers").status_code == 401
    assert client.post("/api/suppliers", json={"name": "No Auth"}).status_code == 401
    for method in ("post", "patch", "delete"):
        path = "/api/suppliers" if method == "post" else "/api/suppliers/999"
        response = client.request(method.upper(), path, headers=staff_headers,
                                  json={"name": "Staff Supplier"} if method == "post" else {})
        assert response.status_code == 403
    assert client.get("/api/suppliers", headers=staff_headers).status_code == 200


def test_supplier_crud_search_filter_pagination_and_audit(client, owner_headers, db_session):
    prefix = "Suppliers API"
    for name, phone in ((f"{prefix} Alpha", "111-333"),
                        (f"{prefix} Beta", "222-444"),
                        (f"{prefix} Gamma", "333-555")):
        response = client.post("/api/suppliers", headers=owner_headers, json={
            "name": name, "phone": phone, "email": f"{phone.replace('-', '')}@example.org",
            "contact_person": "Casey Supplier",
        })
        assert response.status_code == 201
    assert client.get("/api/suppliers", headers=owner_headers, params={"q": "222"}).json()["data"]["total"] == 1
    assert client.get("/api/suppliers", headers=owner_headers, params={"q": "Casey"}).json()["data"]["total"] == 3
    listing = client.get("/api/suppliers", headers=owner_headers, params={"q": prefix, "limit": 2, "offset": 1}).json()["data"]
    assert listing["total"] == 3 and len(listing["items"]) == 2
    assert listing["limit"] == 2 and listing["offset"] == 1
    all_items = client.get("/api/suppliers", headers=owner_headers, params={"q": prefix}).json()["data"]["items"]
    supplier = next(item for item in all_items if item["name"].endswith("Alpha"))
    sid = supplier["id"]
    assert client.get(f"/api/suppliers/{sid}", headers=owner_headers).json()["data"]["name"].endswith("Alpha")
    updated = client.patch(f"/api/suppliers/{sid}", headers=owner_headers, json={"phone": "999"})
    assert updated.status_code == 200 and updated.json()["data"]["phone"] == "999"
    assert client.delete(f"/api/suppliers/{sid}", headers=owner_headers).status_code == 200
    gamma = next(item for item in all_items if item["name"].endswith("Gamma"))
    assert client.delete(f"/api/suppliers/{gamma['id']}", headers=owner_headers).status_code == 200
    assert client.get("/api/suppliers", headers=owner_headers, params={"q": prefix, "is_active": False}).json()["data"]["total"] == 2
    actions = list(db_session.scalars(select(AuditLog.action).where(
        AuditLog.entity_type == ENTITY_TYPE_SUPPLIER, AuditLog.entity_id == sid
    )))
    assert set(actions) == {"CREATE", "UPDATE", "DELETE"}


def test_supplier_conflicts_missing_and_validation(client, owner_headers):
    payload = {"name": "Unique Supplier API", "email": "valid@example.org"}
    assert client.post("/api/suppliers", headers=owner_headers, json=payload).status_code == 201
    assert client.post("/api/suppliers", headers=owner_headers, json=payload).status_code == 409
    assert client.post("/api/suppliers", headers=owner_headers, json={"name": "   "}).status_code == 422
    assert client.post("/api/suppliers", headers=owner_headers, json={"name": "Bad Email", "email": "bad"}).status_code == 422
    assert client.get("/api/suppliers/999999", headers=owner_headers).status_code == 404
    assert client.patch("/api/suppliers/999999", headers=owner_headers, json={"name": "No Such"}).status_code == 404
    assert client.delete("/api/suppliers/999999", headers=owner_headers).status_code == 404
