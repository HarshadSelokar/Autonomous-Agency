"""
Unit tests for GroqModelProvider using mocks.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.exceptions import AuthenticationError, ConfigurationError, RateLimitError
from src.domain.model_provider import ChatMessage, ModelRequest
from src.infrastructure.providers.groq_provider import GroqModelProvider


def test_groq_provider_unconfigured_api_key_raises_error() -> None:
    provider = GroqModelProvider(api_key="")
    request = ModelRequest(model="llama-3.3-70b-versatile", messages=[])

    with pytest.raises(ConfigurationError) as exc_info:
        # Calling generate without API key should raise ConfigurationError
        import asyncio
        asyncio.run(provider.generate(request))

    assert "Groq API Key is not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_groq_provider_successful_response(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = GroqModelProvider(api_key="gsk_fake_key_for_unit_tests")

    # Mock AsyncGroq response
    mock_completion = MagicMock()
    mock_completion.id = "groq_req_123"
    mock_completion.model = "llama-3.3-70b-versatile"
    mock_choice = MagicMock()
    mock_choice.message.content = "Groq output response"
    mock_choice.finish_reason = "stop"
    mock_completion.choices = [mock_choice]
    mock_completion.usage.prompt_tokens = 15
    mock_completion.usage.completion_tokens = 25
    mock_completion.usage.total_tokens = 40

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
    provider._client = mock_client

    request = ModelRequest(
        model="llama-3.3-70b-versatile",
        messages=[ChatMessage(role="user", content="Explain Groq architecture.")],
    )

    response = await provider.generate(request)

    assert response.provider == "groq"
    assert response.content == "Groq output response"
    assert response.usage.input_tokens == 15
    assert response.usage.output_tokens == 25
    assert response.usage.total_tokens == 40
    assert response.request_id == "groq_req_123"


@pytest.mark.asyncio
async def test_groq_provider_maps_rate_limit_error() -> None:
    import groq

    provider = GroqModelProvider(api_key="gsk_fake_key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_client.chat.completions.create = AsyncMock(
        side_effect=groq.RateLimitError("Rate limit", response=mock_response, body=None)
    )
    provider._client = mock_client

    with pytest.raises(RateLimitError):
        await provider.generate(ModelRequest(model="llama-3.3-70b-versatile", messages=[]))


@pytest.mark.asyncio
async def test_groq_provider_maps_authentication_error() -> None:
    import groq

    provider = GroqModelProvider(api_key="invalid_key")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_client.chat.completions.create = AsyncMock(
        side_effect=groq.AuthenticationError("Auth failed", response=mock_response, body=None)
    )
    provider._client = mock_client

    with pytest.raises(AuthenticationError):
        await provider.generate(ModelRequest(model="llama-3.3-70b-versatile", messages=[]))
