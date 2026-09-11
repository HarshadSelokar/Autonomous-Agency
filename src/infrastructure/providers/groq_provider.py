"""
Groq Model Provider Implementation using official AsyncGroq SDK.
Maps SDK requests/responses and translates provider errors into typed domain exceptions.
"""

import json
from typing import Any

import groq
from groq import AsyncGroq

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


class GroqModelProvider(ModelProviderInterface):
    def __init__(self, api_key: str | None = None, default_model: str | None = None) -> None:
        self.api_key = api_key or settings.GROQ_API_KEY
        self.default_model = default_model or settings.GROQ_MODEL
        self._client: AsyncGroq | None = None

    @property
    def provider_name(self) -> str:
        return "groq"

    def _get_client(self) -> AsyncGroq:
        if self._client is None:
            if not self.api_key:
                raise ConfigurationError(
                    "Groq API Key is not configured. Set GROQ_API_KEY environment variable."
                )
            self._client = AsyncGroq(api_key=self.api_key)
        return self._client

    async def generate(self, request: ModelRequest) -> ModelResponse:
        client = self._get_client()

        model_name = request.model or self.default_model

        messages_payload = [
            {"role": msg.role, "content": msg.content, **({"name": msg.name} if msg.name else {})}
            for msg in request.messages
        ]

        kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages_payload,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "timeout": request.timeout_seconds,
        }

        # If structured output JSON schema is specified
        if request.response_schema is not None:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            chat_completion = await client.chat.completions.create(**kwargs)
        except groq.AuthenticationError as e:
            raise AuthenticationError(f"Groq authentication failed: {e}") from e
        except groq.RateLimitError as e:
            raise RateLimitError(f"Groq rate limit exceeded: {e}") from e
        except groq.APITimeoutError as e:
            raise TimeoutError(f"Groq request timed out: {e}") from e
        except groq.APIConnectionError as e:
            raise ProviderUnavailableError(f"Groq API connection error: {e}") from e
        except groq.APIStatusError as e:
            if e.status_code in (500, 502, 503, 504):
                raise ProviderUnavailableError(f"Groq server error ({e.status_code}): {e}") from e
            raise ModelExecutionError(f"Groq API error ({e.status_code}): {e}") from e
        except Exception as e:
            raise ModelExecutionError(f"Unexpected Groq provider error: {e}") from e

        choice = chat_completion.choices[0]
        content = choice.message.content or ""

        # Normalize usage
        usage_data = chat_completion.usage
        usage_info = UsageInfo(
            input_tokens=getattr(usage_data, "prompt_tokens", 0) if usage_data else 0,
            output_tokens=getattr(usage_data, "completion_tokens", 0) if usage_data else 0,
            total_tokens=getattr(usage_data, "total_tokens", 0) if usage_data else 0,
        )

        # Parse structured output if requested
        structured_output: dict[str, Any] | None = None
        if request.response_schema is not None and content:
            try:
                structured_output = json.loads(content)
            except json.JSONDecodeError:
                structured_output = None

        return ModelResponse(
            content=content,
            provider="groq",
            model=chat_completion.model or model_name,
            usage=usage_info,
            structured_output=structured_output,
            request_id=getattr(chat_completion, "id", ""),
            finish_reason=choice.finish_reason or "stop",
        )
