"""
Application Configuration Module.
Environment-based settings with default fallbacks.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Autonomous AI Company - Agent Runtime"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Groq Model Provider
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TIMEOUT_SECONDS: int = 60

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_runtime"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Execution Engine Defaults
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0
    DEFAULT_RUN_TIMEOUT_SECONDS: int = 300


# Singleton settings instance
settings = Settings()
