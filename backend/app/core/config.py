from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-only-insecure-key-change-me-0123456789"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    log_level: str = "INFO"
    secret_key: str = DEV_SECRET_KEY
    access_token_ttl_min: int = 10080
    database_url: str = "sqlite+aiosqlite:///./signal.db"
    otp_fixed_code: str = "123456"
    cors_origins: str = "http://localhost:3000"
    cors_origin_regex: str | None = None
    upload_dir: str = "./uploads"
    max_upload_bytes: int = 2 * 1024 * 1024
    seed_on_startup: bool = True

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def _forbid_dev_secret_in_production(self) -> "Settings":
        if self.is_production and self.secret_key == DEV_SECRET_KEY:
            raise ValueError("SECRET_KEY must be set to a real secret when ENV=production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
