"""
Unit tests for ModelProviderRegistry.
"""

import pytest

from src.application.provider_registry import ModelProviderRegistry
from src.domain.exceptions import ConfigurationError
from src.infrastructure.models.fake_provider import FakeModelProvider


def test_provider_registry_register_and_get() -> None:
    registry = ModelProviderRegistry()
    fake_provider = FakeModelProvider()

    registry.register(fake_provider)

    assert registry.has("fake")
    assert registry.has("FAKE")  # Case insensitive
    retrieved = registry.get("fake")
    assert retrieved is fake_provider


def test_provider_registry_missing_provider_raises_error() -> None:
    registry = ModelProviderRegistry()

    with pytest.raises(ConfigurationError) as exc_info:
        registry.get("unknown_provider")

    assert "Model provider 'unknown_provider' is not registered" in str(exc_info.value)
