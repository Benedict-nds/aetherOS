from app.core.permissions import can_assign_role, can_modify_user


class DummyRole:
    def __init__(self, name: str):
        self.name = name


class DummyUser:
    def __init__(self, user_id: int, role_name: str):
        self.id = user_id
        self.role = DummyRole(role_name)


def test_admin_cannot_assign_owner():
    actor = DummyUser(1, "admin")
    assert can_assign_role(actor, "owner") is False
    assert can_assign_role(actor, "pharmacist") is True


def test_owner_can_assign_all_roles():
    actor = DummyUser(1, "owner")
    assert can_assign_role(actor, "owner") is True
    assert can_assign_role(actor, "staff") is True


def test_admin_cannot_modify_owner_user():
    actor = DummyUser(1, "admin")
    target = DummyUser(2, "owner")
    assert can_modify_user(actor, target) is False
