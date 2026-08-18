from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.responses import error_response, success_response
from app.core.security import get_current_user
from app.models.user import User
from app.modules.auth.schemas import LoginRequest
from app.modules.auth.service import authenticate_user, create_user_token

router = APIRouter()


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "username": user.username,
        "role": user.role.name,
    }


@router.post("/login")
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        payload.email,
        payload.password,
    )

    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response("Invalid credentials"),
        )

    token = create_user_token(user)

    return success_response(
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": serialize_user(user),
        },
        message="Logged in",
    )


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
):
    return success_response(
        data=None,
        message="Logged out",
    )


@router.get("/me")
def me(
    current_user: User = Depends(get_current_user),
):
    return success_response(
        data=serialize_user(current_user),
        message="Current user",
    )
