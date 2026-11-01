"""Production Environment Settings Validation.

Validates that production environments do not launch with default secrets or invalid configuration.
"""

import logging
from src.infrastructure.config import Settings

logger = logging.getLogger(__name__)


def validate_production_env(config: Settings) -> None:
    """Validates configuration parameters for production readiness.
    
    Fails fast with ValueError if critical production settings are missing or insecure.
    """
    if config.APP_ENV.lower() != "production":
        return

    logger.info("Validating production environment configuration...")

    errors: list[str] = []

    # 1. Debug mode must be disabled in production
    if config.DEBUG:
        errors.append("DEBUG mode must be set to False in production.")

    # 2. Database validation
    if "sqlite" in config.DATABASE_URL.lower():
        errors.append("SQLite is not supported for production. Use PostgreSQL (postgresql+asyncpg://...).")

    if "postgres:postgres@" in config.DATABASE_URL.lower():
        errors.append("Insecure default database credentials detected in DATABASE_URL.")

    # 3. Model Provider Credentials
    if not config.GROQ_API_KEY and not config.OPENAI_API_KEY:
        errors.append("GROQ_API_KEY or OPENAI_API_KEY is required in production environment.")

    # 3b. Authentication
    if not config.AUTH_REQUIRED:
        errors.append("AUTH_REQUIRED must be true in production.")
    if len(config.AUTH_SECRET_KEY) < 32:
        errors.append("AUTH_SECRET_KEY must be set to at least 32 characters in production.")

    # 4. Storage Validation
    if config.STORAGE_TYPE.lower() == "s3":
        if not config.S3_ACCESS_KEY_ID or not config.S3_SECRET_ACCESS_KEY:
            errors.append("S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY are required when STORAGE_TYPE='s3'.")

    # 5. Security CORS & Hosts
    if "*" in config.CORS_ALLOWED_ORIGINS:
        logger.warning("CORS_ALLOWED_ORIGINS contains wildcard '*' in production.")

    if errors:
        error_msg = "Production Environment Configuration Validation Failed:\n- " + "\n- ".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("Production environment configuration validated successfully.")
