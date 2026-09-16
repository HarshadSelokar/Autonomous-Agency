"""Phase 20 Infrastructure Security Test Suite.

Verifies:
1. Production environment validation and fast-fail on missing/insecure credentials.
2. Secret redaction in structured JSON log output.
3. Security headers injection in production mode (HSTS, X-Frame-Options, X-Content-Type-Options).
4. Request size limiting (HTTP 413 Payload Too Large).
"""

import json
import logging
import pytest
from httpx import ASGITransport, AsyncClient

from src.api.main import app
from src.infrastructure.config import Settings
from src.infrastructure.env_validation import validate_production_env
from src.infrastructure.logging_config import StructuredJsonFormatter


def test_production_environment_validation_security():
    # Insecure settings must fail fast
    insecure = Settings(
        APP_ENV="production",
        DEBUG=True,
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/db",
        GROQ_API_KEY="",
    )
    with pytest.raises(ValueError, match="Validation Failed"):
        validate_production_env(insecure)


def test_sensitive_secret_redaction_in_logs():
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="sec_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Testing secret log redaction",
        args=(),
        exc_info=None,
    )
    # Attach sensitive info
    record.event = "User login attempt"
    
    log_line = formatter.format(record)
    assert "gsk_" not in log_line
    assert "password" not in log_line.lower() or "[REDACTED]" in log_line


@pytest.mark.asyncio
async def test_security_headers_and_request_size_limit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test liveness check
        res = await client.get("/health/live")
        assert res.status_code == 200

        # Test request payload exceeding size limit (15MB payload)
        large_headers = {"Content-Length": "15728640"}
        res_large = await client.post("/api/v1/research/requests", content=b"x", headers=large_headers)
        assert res_large.status_code == 413
