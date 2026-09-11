"""
Sanity check test for project setup and configuration loading.
"""

from src.infrastructure.config import settings


def test_settings_load() -> None:
    assert settings.APP_NAME == "Autonomous AI Company - Agent Runtime"
    assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"
    assert settings.MAX_RETRIES == 3
