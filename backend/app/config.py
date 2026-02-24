from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "easyQuant API"
    PROJECT_DESCRIPTION: str = "easyQuant Backend API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/easyquant"

    REDIS_URL: str = "redis://localhost:6379/0"

    DEBUG: bool = False

    AKSHARE_RATE_LIMIT_QPS: float = 0.5
    AKSHARE_RATE_LIMIT_BURST: int = 3
    AKSHARE_RETRY_MAX_ATTEMPTS: int = 3
    AKSHARE_RETRY_BASE_DELAY: float = 2.0
    AKSHARE_RETRY_MAX_DELAY: float = 120.0


settings = Settings()
