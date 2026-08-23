from pydantic_settings import BaseSettings, SettingsConfigDict


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

    demo_email: str = "admin@aetherqore.local"
    demo_password: str = "Admin123!"
    demo_full_name: str = "Pharmacy Admin"
    demo_username: str = "admin"
    demo_role: str = "owner"


settings = Settings()
