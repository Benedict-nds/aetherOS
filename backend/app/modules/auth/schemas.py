from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()

        local_part, _, domain = value.partition("@")

        if not local_part or not domain:
            raise ValueError("Invalid email address")

        return value


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    username: str
    role: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse