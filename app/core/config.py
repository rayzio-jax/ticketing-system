"""Global configs."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Ticketing API"
    database_url: str
    jwt_algorithm: str
    jwt_secret: str
    access_token_expiration_minutes: int
    refresh_token_expiration_days: int
    booking_expire_minutes: int


settings = Settings()  # pyright: ignore[reportCallIssue]
