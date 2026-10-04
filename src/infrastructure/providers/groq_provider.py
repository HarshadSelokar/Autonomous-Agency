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
    ToolCallRejectedError,
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


DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


class GroqModelProvider(ModelProviderInterface):
    def __init__(self, api_key: str | None = None, default_model: str | None = None) -> None:
        # An explicit empty key means "unconfigured"; only None falls back to settings
        self.api_key = api_key if api_key is not None else settings.GROQ_API_KEY
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

        # GROQ_MODEL="" in an env file overrides the settings default with an empty string
        model_name = request.model or self.default_model or DEFAULT_GROQ_MODEL

        kwargs: dict[str, Any] = {
            "model": model_name,
            "messages": messages_to_payload(request.messages),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "timeout": request.timeout_seconds,
        }

        if request.tools:
            kwargs["tools"] = tools_to_payload(request.tools)
            kwargs["tool_choice"] = "auto"

        # If structured output JSON schema is specified (JSON mode cannot be combined with tools)
        if request.response_schema is not None and not request.tools:
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
            error = (e.body or {}).get("error") if isinstance(getattr(e, "body", None), dict) else None
            if isinstance(error, dict) and error.get("code") == "tool_use_failed":
                raise ToolCallRejectedError(
                    f"Groq rejected the tool call: {error.get('message', '')}",
                    failed_generation=str(error.get("failed_generation") or ""),
                ) from e
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
            tool_calls=parse_tool_calls(getattr(choice.message, "tool_calls", None)),
            request_id=getattr(chat_completion, "id", ""),
            finish_reason=choice.finish_reason or "stop",
        )
