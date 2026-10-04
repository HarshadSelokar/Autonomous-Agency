"""
Deterministic Fake Model Provider for Testing and Failure Injection.
"""

from typing import Any

from src.domain.exceptions import (
    AuthenticationError,
    InvalidResponseError,
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


class FakeModelProvider(ModelProviderInterface):
    def __init__(
        self,
        canned_content: str = "This is a deterministic fake response.",
        canned_structured_output: dict[str, Any] | None = None,
        canned_usage: UsageInfo | None = None,
        should_fail_with: Exception | None = None,
    ) -> None:
        self._canned_content = canned_content
        self._canned_structured_output = canned_structured_output
        self._canned_usage = canned_usage or UsageInfo(
            input_tokens=10, output_tokens=20, total_tokens=30
        )
        self._should_fail_with = should_fail_with
        self._scripted_responses: list[ModelResponse] = []
        self.call_count: int = 0
        self.last_request: ModelRequest | None = None
        self.requests: list[ModelRequest] = []

    def script(
        self,
        content: str = "",
        tool_calls: list[dict[str, Any]] | None = None,
        structured_output: dict[str, Any] | None = None,
    ) -> None:
        """Queue one response; queued responses are returned in order before the canned one."""
        self._scripted_responses.append(
            ModelResponse(
                content=content,
                provider="fake",
                model="fake",
                usage=self._canned_usage,
                structured_output=structured_output,
                tool_calls=tool_calls or [],
                finish_reason="tool_calls" if tool_calls else "stop",
            )
        )

    @property
    def provider_name(self) -> str:
        return "fake"

    def set_canned_response(
        self,
        content: str,
        structured_output: dict[str, Any] | None = None,
        usage: UsageInfo | None = None,
    ) -> None:
        self._canned_content = content
        self._canned_structured_output = structured_output
        if usage is not None:
            self._canned_usage = usage

    def set_failure(self, exception: Exception | None) -> None:
        self._should_fail_with = exception

    async def generate(self, request: ModelRequest) -> ModelResponse:
        self.call_count += 1
        self.last_request = request
        self.requests.append(request)

        if self._should_fail_with is not None:
            raise self._should_fail_with

        # Simulate exception types based on model name flags if requested
        if request.model == "simulate-timeout":
            raise TimeoutError("Fake timeout occurred")
        if request.model == "simulate-rate-limit":
            raise RateLimitError("Fake rate limit exceeded")
        if request.model == "simulate-unavailable":
            raise ProviderUnavailableError("Fake provider unavailable")
        if request.model == "simulate-auth-failure":
            raise AuthenticationError("Fake invalid API key")
        if request.model == "simulate-invalid-response":
            raise InvalidResponseError("Fake malformed response")

        if self._scripted_responses:
            return self._scripted_responses.pop(0)

        return ModelResponse(
            content=self._canned_content,
            provider="fake",
            model=request.model,
            usage=self._canned_usage,
            structured_output=self._canned_structured_output,
            request_id=f"fake_req_{self.call_count}",
            finish_reason="stop",
        )
