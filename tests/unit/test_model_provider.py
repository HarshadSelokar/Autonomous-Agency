"""
Unit tests for ModelProvider abstraction and FakeModelProvider.
"""

import pytest

from src.domain.exceptions import (
    AuthenticationError,
    ProviderUnavailableError,
    RateLimitError,
    TimeoutError,
)
from src.domain.model_provider import ChatMessage, ModelRequest
from src.infrastructure.models.fake_provider import FakeModelProvider


@pytest.mark.asyncio
async def test_fake_model_provider_successful_generate() -> None:
    provider = FakeModelProvider(canned_content="Hello, AI World!")
    request = ModelRequest(
        model="fake-model",
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Say hello."),
        ],
    )

    response = await provider.generate(request)

    assert response.content == "Hello, AI World!"
    assert response.provider == "fake"
    assert response.model == "fake-model"
    assert response.usage.total_tokens == 30
    assert provider.call_count == 1
    assert provider.last_request == request


@pytest.mark.asyncio
async def test_fake_model_provider_simulated_failures() -> None:
    provider = FakeModelProvider()

    # Timeout
    with pytest.raises(TimeoutError):
        await provider.generate(ModelRequest(model="simulate-timeout", messages=[]))

    # Rate Limit
    with pytest.raises(RateLimitError):
        await provider.generate(ModelRequest(model="simulate-rate-limit", messages=[]))

    # Provider Unavailable
    with pytest.raises(ProviderUnavailableError):
        await provider.generate(ModelRequest(model="simulate-unavailable", messages=[]))

    # Auth failure
    with pytest.raises(AuthenticationError):
        await provider.generate(ModelRequest(model="simulate-auth-failure", messages=[]))


@pytest.mark.asyncio
async def test_fake_model_provider_custom_exception() -> None:
    provider = FakeModelProvider(should_fail_with=RateLimitError("Quota exceeded"))

    with pytest.raises(RateLimitError) as exc:
        await provider.generate(ModelRequest(model="test", messages=[]))

    assert "Quota exceeded" in str(exc.value)
