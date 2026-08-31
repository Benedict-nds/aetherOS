from pydantic import BaseModel, Field, field_validator


def _normalize_email(value: str) -> str:
    value = value.strip().lower()

    local_part, _, domain = value.partition("@")

    if not local_part or not domain:
        raise ValueError("Invalid email address")

    return value


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    email: str = Field(max_length=255)
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(min_length=1, max_length=50)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    email: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, min_length=3, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: str | None = Field(default=None, min_length=1, max_length=50)
    status: str | None = Field(default=None, pattern="^(active|inactive)$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_email(value)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    username: str
    role: str
    status: str
    last_login_at: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = {"from_attributes": True}
