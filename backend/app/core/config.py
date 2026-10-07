from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    secret_key: str = "dev-only-insecure-key"
    access_token_ttl_min: int = 10080
    database_url: str = "sqlite+aiosqlite:///./signal.db"
    otp_fixed_code: str = "123456"
    cors_origins: str = "http://localhost:3000"
    cors_origin_regex: str | None = None
    upload_dir: str = "./uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
