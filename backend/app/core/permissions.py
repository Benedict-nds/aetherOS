from collections.abc import Callable
from enum import IntEnum

from fastapi import Depends, HTTPException, status

from app.core.responses import error_response
from app.core.security import get_current_user
from app.models.user import User

ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_PHARMACIST = "pharmacist"
ROLE_STAFF = "staff"

SYSTEM_ROLES = frozenset({ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST, ROLE_STAFF})

USER_STATUSES = frozenset({"active", "inactive"})


class RoleRank(IntEnum):
    staff = 1
    pharmacist = 2
    admin = 3
    owner = 4


ROLE_RANKS: dict[str, RoleRank] = {
    ROLE_STAFF: RoleRank.staff,
    ROLE_PHARMACIST: RoleRank.pharmacist,
    ROLE_ADMIN: RoleRank.admin,
    ROLE_OWNER: RoleRank.owner,
}


def get_role_rank(role_name: str) -> RoleRank | None:
    return ROLE_RANKS.get(role_name)


def require_roles(*allowed_roles: str) -> Callable[..., User]:
    allowed = frozenset(allowed_roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response("Insufficient permissions"),
            )
        return current_user

    return dependency


def can_manage_users(actor: User) -> bool:
    return actor.role.name in {ROLE_OWNER, ROLE_ADMIN}


def can_assign_role(actor: User, target_role_name: str) -> bool:
    actor_rank = get_role_rank(actor.role.name)
    target_rank = get_role_rank(target_role_name)

    if actor_rank is None or target_rank is None:
        return False

    if actor.role.name == ROLE_ADMIN and target_role_name == ROLE_OWNER:
        return False

    return target_rank.value <= actor_rank.value


def can_modify_user(actor: User, target: User) -> bool:
    if not can_manage_users(actor):
        return False

    if actor.id == target.id:
        return True

    if target.role.name == ROLE_OWNER and actor.role.name != ROLE_OWNER:
        return False

    if actor.role.name == ROLE_ADMIN:
        target_rank = get_role_rank(target.role.name)
        if target_rank is not None and target_rank.value >= RoleRank.admin.value:
            if target.role.name == ROLE_OWNER:
                return False

    return can_assign_role(actor, target.role.name)
