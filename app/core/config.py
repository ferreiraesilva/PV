from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = Field("safv", description="Application identifier used in logs and metrics")
    environment: str = Field("development", description="Deployment environment name")

    secret_key: str = Field("change_this_secret_key", description="JWT signing secret")
    algorithm: str = Field("HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(30, description="Access token expiration in minutes")
    refresh_token_expire_minutes: int = Field(43200, description="Refresh token expiration in minutes")

    database_url: str = Field(
        "postgresql+psycopg2://app_user:change_me@localhost:5432/pv",
        description="SQLAlchemy database URL",
    )
    database_echo: bool = Field(False, description="Enable SQLAlchemy echo logging")

    log_level: str = Field("INFO", description="Application log level")
    cors_origins: str = Field("*", description="Comma separated list of allowed CORS origins")
    metrics_namespace: str = Field("safv", description="Metrics namespace prefix")

    rate_limit_requests: int = Field(100, ge=1, description="Maximum requests allowed per window per client")
    rate_limit_window_seconds: int = Field(60, ge=1, description="Window size in seconds for rate limiting")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
