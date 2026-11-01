"""
Provider-Neutral Model Provider Domain Abstraction.
Pure domain interfaces and normalized response data structures.
Zero dependencies on Groq, OpenAI, or external SDKs.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChatMessage:
    role: str  # system, user, assistant, tool
    content: str
    name: str | None = None
    # Assistant turns that request tools carry normalized calls: {"id", "name", "arguments"}
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    # Tool result turns reference the call they answer
    tool_call_id: str | None = None


@dataclass(frozen=True)
class UsageInfo:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class ModelRequest:
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    response_schema: dict[str, Any] | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    timeout_seconds: float = 60.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponse:
    content: str
    provider: str
    model: str
    usage: UsageInfo
    structured_output: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    request_id: str = ""
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProviderInterface(ABC):
    """Abstract interface for LLM Model Providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifier of the model provider (e.g., 'groq', 'fake')."""
        pass

    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        """Execute a model generation request and return a normalized ModelResponse."""
        pass
