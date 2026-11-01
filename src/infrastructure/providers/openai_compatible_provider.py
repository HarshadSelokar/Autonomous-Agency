"""
OpenAI-compatible Model Provider (chat-completions over HTTP).
Works with OpenAI and any gateway exposing the same API (OpenRouter, Ollama, vLLM, ...)
by pointing OPENAI_BASE_URL at it.
"""

import json
from typing import Any

import httpx

from src.domain.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ModelExecutionError,
    ProviderUnavailableError,
    RateLimitError,
    TimeoutError,
)
from src.domain.model_provider import (
    ModelProviderInterface,
    ModelRequest,
    ModelResponse,
    UsageInfo,
)
from src.infrastructure.config import settings
from src.infrastructure.providers.openai_format import (
    messages_to_payload,
    parse_tool_calls,
    tools_to_payload,
)


class OpenAICompatibleModelProvider(ModelProviderInterface):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str | None = None,
        name: str = "openai",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.OPENAI_MODEL
        self._name = name
        self._transport = transport

    @property
    def provider_name(self) -> str:
        return self._name

    async def generate(self, request: ModelRequest) -> ModelResponse:
        if not self.api_key:
            raise ConfigurationError(
                f"API key for provider '{self._name}' is not configured. "
                "Set OPENAI_API_KEY environment variable."
            )

        model_name = request.model or self.default_model
        body: dict[str, Any] = {
            "model": model_name,
            "messages": messages_to_payload(request.messages),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
        }
        if request.tools:
            body["tools"] = tools_to_payload(request.tools)
            body["tool_choice"] = "auto"
        if request.response_schema is not None and not request.tools:
            body["response_format"] = {"type": "json_object"}

        try:
            async with httpx.AsyncClient(
                timeout=request.timeout_seconds, transport=self._transport
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
        except httpx.TimeoutException as e:
            raise TimeoutError(f"{self._name} request timed out: {e}") from e
        except httpx.HTTPError as e:
            raise ProviderUnavailableError(f"{self._name} API connection error: {e}") from e

        if response.status_code in (401, 403):
            raise AuthenticationError(f"{self._name} authentication failed ({response.status_code}).")
        if response.status_code == 429:
            raise RateLimitError(f"{self._name} rate limit exceeded.")
        if response.status_code >= 500:
            raise ProviderUnavailableError(f"{self._name} server error ({response.status_code}).")
        if response.status_code >= 400:
            raise ModelExecutionError(
                f"{self._name} API error ({response.status_code}): {response.text[:500]}"
            )

        try:
            data = response.json()
            choice = data["choices"][0]
            message = choice.get("message") or {}
        except (ValueError, KeyError, IndexError) as e:
            raise ModelExecutionError(f"{self._name} returned a malformed response: {e}") from e

        content = message.get("content") or ""
        usage = data.get("usage") or {}

        structured_output: dict[str, Any] | None = None
        if request.response_schema is not None and content:
            try:
                structured_output = json.loads(content)
            except json.JSONDecodeError:
                structured_output = None

        return ModelResponse(
            content=content,
            provider=self._name,
            model=data.get("model") or model_name,
            usage=UsageInfo(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
            structured_output=structured_output,
            tool_calls=parse_tool_calls(message.get("tool_calls")),
            request_id=data.get("id", ""),
            finish_reason=choice.get("finish_reason") or "stop",
        )
