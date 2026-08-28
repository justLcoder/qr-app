from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./qr_studio.db"
    secret_key: str = "development-only-change-me"
    public_base_url: str = "http://localhost:8000"
    frontend_origin: str = "http://localhost:5173"
    access_token_minutes: int = 60 * 24 * 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
