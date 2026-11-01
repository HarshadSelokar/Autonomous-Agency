"""Unit tests for configuration system and production environment validation."""

import pytest
from src.infrastructure.config import Settings
from src.infrastructure.env_validation import validate_production_env


def test_development_config_validation():
    dev_settings = Settings(
        APP_ENV="development",
        DEBUG=True,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
    )
    # Should not raise any error in development mode
    validate_production_env(dev_settings)


def test_production_config_validation_pass():
    prod_settings = Settings(
        APP_ENV="production",
        DEBUG=False,
        DATABASE_URL="postgresql+asyncpg://prod_user:secure_pass_123@prod-db.internal:5432/agency_db",
        GROQ_API_KEY="gsk_real_production_key_sample",
        STORAGE_TYPE="local",
        AUTH_REQUIRED=True,
        AUTH_SECRET_KEY="a-production-signing-secret-of-sufficient-length",
    )
    # Valid production settings should pass without error
    validate_production_env(prod_settings)


def test_production_requires_authentication():
    no_auth_settings = Settings(
        APP_ENV="production",
        DEBUG=False,
        DATABASE_URL="postgresql+asyncpg://prod_user:secure_pass_123@prod-db.internal:5432/agency_db",
        GROQ_API_KEY="gsk_real_production_key_sample",
        STORAGE_TYPE="local",
        AUTH_REQUIRED=False,
        AUTH_SECRET_KEY="",
    )
    with pytest.raises(ValueError, match="AUTH_REQUIRED must be true"):
        validate_production_env(no_auth_settings)


def test_production_config_validation_failures():
    bad_prod_settings = Settings(
        APP_ENV="production",
        DEBUG=True,  # Bad: DEBUG is True
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/agent_runtime",  # Bad: default creds
        GROQ_API_KEY="",  # Bad: missing key
    )
    with pytest.raises(ValueError, match="Production Environment Configuration Validation Failed"):
        validate_production_env(bad_prod_settings)


def test_production_s3_storage_validation_failure():
    bad_s3_settings = Settings(
        APP_ENV="production",
        DEBUG=False,
        DATABASE_URL="postgresql+asyncpg://prod_user:secure_pass_123@prod-db.internal:5432/agency_db",
        GROQ_API_KEY="gsk_valid_key",
        STORAGE_TYPE="s3",
        S3_ACCESS_KEY_ID=None,  # Missing S3 keys
    )
    with pytest.raises(ValueError, match="S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY are required"):
        validate_production_env(bad_s3_settings)
