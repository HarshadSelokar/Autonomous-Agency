"""Application Configuration Module.

Environment-based settings with default fallbacks and production validation.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Autonomous AI Company - Agent Runtime"
    APP_ENV: str = Field(default="development", description="development, test, staging, production")
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Groq Model Provider
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_TIMEOUT_SECONDS: int = 60

    # OpenAI-compatible Model Provider (OpenAI, OpenRouter, Ollama, ...)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"

    # Authentication
    AUTH_REQUIRED: bool = True
    AUTH_SECRET_KEY: str = ""
    AUTH_TOKEN_TTL_MINUTES: int = 480
    ADMIN_API_KEY: str = ""

    # Software Studio (autonomous dev team)
    STUDIO_WORKSPACES_DIR: str = "scratch/studio"
    # "loop" = our agent loop on a model provider (API key); "agy" = Antigravity CLI (subscription)
    STUDIO_ENGINE: str = "loop"
    STUDIO_PROVIDER: str = "groq"
    STUDIO_MODEL: str = ""
    STUDIO_MAX_AGENT_STEPS: int = 30
    STUDIO_MAX_REWORK_ROUNDS: int = 2
    STUDIO_COMMAND_TIMEOUT_SECONDS: int = 300
    # Antigravity CLI engine
    AGY_COMMAND: str = "agy"
    AGY_MODEL_MANAGER: str = "gemini-3.1-pro-high"
    AGY_MODEL_DEVELOPER: str = "gemini-3.8-flash-high"
    AGY_MODEL_REVIEWER: str = "gemini-3.1-pro-low"
    AGY_FALLBACK_MODEL: str = "gemini-3.7-flash-medium"
    AGY_TIMEOUT_MINUTES: int = 20
    # Substrings (case-insensitive) of an agy error that mean "this model is out of quota"
    AGY_QUOTA_MARKERS: list[str] = Field(
        default_factory=lambda: ["quota", "rate limit", "resource_exhausted", "resource exhausted", "429"]
    )
    # How many developers work tickets at the same time, each in its own git worktree
    STUDIO_DEVELOPERS: int = 2
    # When every model is out of quota the project waits this long, then resumes by itself
    STUDIO_QUOTA_RETRY_MINUTES: int = 30
    # Restart projects that were running when the API process stopped
    STUDIO_AUTO_RESUME: bool = True
    # Seconds between checks for a human decision on a ticket awaiting approval
    STUDIO_APPROVAL_POLL_SECONDS: float = 2.0

    STUDIO_ALLOWED_COMMANDS: list[str] = Field(
        default_factory=lambda: [
            "python", "python3", "pytest", "pip", "uv", "ruff", "mypy",
            "node", "npm", "npx", "pnpm", "yarn", "tsc",
            "go", "cargo", "make", "git",
        ]
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_runtime"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: float = 5.0
    REDIS_RETRY_ON_TIMEOUT: bool = True

    # Storage Provider Configuration
    STORAGE_TYPE: str = Field(default="local", description="local or s3")
    S3_ENDPOINT_URL: str | None = None
    S3_BUCKET_NAME: str = "autonomous-artifacts"
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_REGION: str = "us-east-1"
    LOCAL_STORAGE_DIR: str = "scratch/artifact_storage"

    # Background Worker Configuration
    WORKER_CONCURRENCY: int = 10
    WORKER_DRAIN_TIMEOUT: int = 30
    WORKER_POLL_INTERVAL_SECONDS: float = 1.0

    # API & Security
    CORS_ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    RATE_LIMIT_PER_MINUTE: int = 120
    MAX_CONTENT_LENGTH_BYTES: int = 10485760  # 10 MB limit
    TRUSTED_PROXIES: list[str] = Field(default_factory=lambda: ["127.0.0.1"])

    # Observability & Telemetry
    OTEL_SERVICE_NAME: str = "autonomous-agency-platform"
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None
    PROMETHEUS_METRICS_ENABLED: bool = True

    # Execution Engine Defaults
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0
    DEFAULT_RUN_TIMEOUT_SECONDS: int = 300


# Singleton settings instance
settings = Settings()
