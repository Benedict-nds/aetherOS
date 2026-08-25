from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AetherQore Pharmacy OS"
    environment: str = "development"
    debug: bool = True

    secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 8

    database_url: str

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    demo_email: str = "admin@aetherqore.local"
    demo_password: str = "Admin123!"
    demo_full_name: str = "Pharmacy Admin"
    demo_username: str = "admin"
    demo_role: str = "owner"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
