"""Typed application configuration loaded from environment variables.

``Settings`` is the single place that names runtime settings shared by the
backend, such as the database URL, JWT signing secret, and browser origin.
Other modules call ``get_settings`` rather than reading environment variables
themselves, which keeps configuration consistent across the process.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic reads a local .env file for development and ignores unrelated
    # environment variables rather than treating them as configuration errors.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./qr_studio.db"
    secret_key: str = "development-only-change-me"
    public_base_url: str = "http://localhost:8000"
    frontend_origin: str = "http://localhost:5173"
    access_token_minutes: int = 60 * 24 * 7


@lru_cache
def get_settings() -> Settings:
    # Settings are process-wide and should not be reparsed for each request.
    return Settings()
