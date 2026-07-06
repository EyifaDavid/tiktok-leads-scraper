from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./saas.db"
    jwt_secret: str = "change-me-to-a-real-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    free_quota: int = 50
    pro_quota: int = 500
    enterprise_quota: int = 99999

    scraper_headless: bool = True
    scraper_min_delay: float = 5.0
    scraper_max_delay: float = 15.0


@lru_cache()
def get_settings() -> Settings:
    return Settings()
