"""
Agent Loop: the multi-step think -> tool -> observe cycle.

The single-shot AgentExecutionEngine makes one model call per run. Real work (reading a
codebase, editing files, running tests) needs the model to act, see the result and act
again. AgentLoop drives that cycle against any registered model provider and any toolbox,
bounded by a step limit and an optional cancellation check.
"""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from src.application.provider_registry import ModelProviderRegistry, default_provider_registry
from src.application.retry import RetryPolicy
from src.domain.exceptions import CancellationError, ModelExecutionError
from src.domain.model_provider import ChatMessage, ModelRequest

EventSink = Callable[[dict[str, Any]], Awaitable[None]]
MAX_REJECTED_TOOL_CALLS = 2


def _is_rejected_tool_call(exc: Exception) -> bool:
    text = str(exc).lower()
    return "tool call validation failed" in text or "tool_use_failed" in text


@dataclass
class ToolOutcome:
    content: str
    is_error: bool = False
    # Short human-readable line for status displays, e.g. "running tests"
    summary: str = ""


class AgentToolbox(Protocol):
    def specs(self) -> list[dict[str, Any]]:
        """Tool specs as {"name", "description", "parameters"} (JSON schema)."""
        ...

    def describe(self, name: str, arguments: dict[str, Any]) -> str:
        """Short present-tense description of a call for status displays."""
        ...

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolOutcome: ...


@dataclass
class AgentLoopResult:
    final_text: str
    stop_reason: str  # completed | max_steps | cancelled
    steps: int = 0
    tool_calls: int = 0
    usage: dict[str, int] = field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )
    messages: list[ChatMessage] = field(default_factory=list)
    # Arguments of the final tool, when the run ended by calling it
    final_payload: dict[str, Any] | None = None
    # Actions the engine saw but could not prevent, e.g. a write outside the project
    violations: list[str] = field(default_factory=list)

    @property
    def completed(self) -> bool:
        return self.stop_reason == "completed"


class AgentLoop:
    def __init__(
        self,
        provider_registry: ModelProviderRegistry | None = None,
        retry_policy: RetryPolicy | None = None,
        max_steps: int = 30,
        max_context_chars: int = 120_000,
    ) -> None:
        self.provider_registry = provider_registry or default_provider_registry
        self.retry_policy = retry_policy or RetryPolicy()
        self.max_steps = max_steps
        self.max_context_chars = max_context_chars

    async def run(
        self,
        *,
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        toolbox: AgentToolbox,
        on_event: EventSink | None = None,
        should_cancel: Callable[[], bool] | None = None,
        final_tool: dict[str, Any] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout_seconds: float = 120.0,
    ) -> AgentLoopResult:
        """
        Run until the model answers in text, or calls `final_tool` (a tool spec whose
        arguments are the structured answer, returned as result.final_payload).
        """
        model_provider = self.provider_registry.get(provider)
        tools = toolbox.specs() + ([final_tool] if final_tool else [])
        rejected_calls = 0
        messages: list[ChatMessage] = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]
        result = AgentLoopResult(final_text="", stop_reason="max_steps", messages=messages)

        async def emit(event: dict[str, Any]) -> None:
            if on_event is not None:
                await on_event(event)

        while result.steps < self.max_steps:
            if should_cancel is not None and should_cancel():
                result.stop_reason = "cancelled"
                raise CancellationError("Agent loop cancelled.")

            result.steps += 1
            await emit({"type": "thinking", "step": result.steps})

            request = ModelRequest(
                model=model,
                messages=self._fit_context(messages),
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                timeout_seconds=timeout_seconds,
            )
            try:
                response = await self.retry_policy.execute(
                    lambda request=request: model_provider.generate(request)
                )
            except ModelExecutionError as exc:
                # Some providers reject a malformed or unknown tool call with an error instead
                # of returning it. Tell the model what happened and let it try again.
                if not _is_rejected_tool_call(exc) or rejected_calls >= MAX_REJECTED_TOOL_CALLS:
                    raise
                rejected_calls += 1
                messages.append(
                    ChatMessage(
                        role="user",
                        content=(
                            f"Your last tool call was rejected by the API: {str(exc)[:400]}\n"
                            f"Call only these tools, with valid JSON arguments: "
                            f"{', '.join(tool['name'] for tool in tools)}."
                        ),
                    )
                )
                continue
            result.usage["input_tokens"] += response.usage.input_tokens
            result.usage["output_tokens"] += response.usage.output_tokens
            result.usage["total_tokens"] += response.usage.total_tokens

            if not response.tool_calls:
                messages.append(ChatMessage(role="assistant", content=response.content))
                result.final_text = response.content
                result.stop_reason = "completed"
                await emit({"type": "final", "step": result.steps, "content": response.content})
                return result

            messages.append(
                ChatMessage(
                    role="assistant", content=response.content, tool_calls=response.tool_calls
                )
            )

            for call in response.tool_calls:
                name, arguments = call["name"], call.get("arguments") or {}
                if final_tool is not None and name == final_tool["name"]:
                    result.final_payload = arguments
                    result.final_text = json.dumps(arguments)
                    result.stop_reason = "completed"
                    await emit({"type": "final", "step": result.steps, "content": result.final_text})
                    return result
                summary = toolbox.describe(name, arguments)
                await emit(
                    {
                        "type": "tool_call",
                        "step": result.steps,
                        "tool": name,
                        "arguments": arguments,
                        "summary": summary,
                    }
                )
                try:
                    outcome = await toolbox.execute(name, arguments)
                except Exception as exc:  # a broken tool must not kill the run
                    outcome = ToolOutcome(content=f"Tool '{name}' raised: {exc}", is_error=True)

                result.tool_calls += 1
                messages.append(
                    ChatMessage(role="tool", content=outcome.content, tool_call_id=call["id"])
                )
                await emit(
                    {
                        "type": "tool_result",
                        "step": result.steps,
                        "tool": name,
                        "is_error": outcome.is_error,
                        "summary": outcome.summary or summary,
                        "preview": outcome.content[:400],
                    }
                )

        await emit({"type": "max_steps", "step": result.steps})
        return result

    def _fit_context(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        """Elide the oldest tool outputs once the transcript outgrows the context budget."""
        total = sum(len(m.content) for m in messages)
        if total <= self.max_context_chars:
            return list(messages)

        fitted = list(messages)
        # Keep the most recent tool results intact; shrink from the oldest forward.
        tool_indexes = [i for i, m in enumerate(fitted) if m.role == "tool"]
        for index in tool_indexes[:-4]:
            if total <= self.max_context_chars:
                break
            original = fitted[index]
            if len(original.content) <= 200:
                continue
            placeholder = "[earlier tool output elided to save context]"
            total -= len(original.content) - len(placeholder)
            fitted[index] = ChatMessage(
                role="tool", content=placeholder, tool_call_id=original.tool_call_id
            )
        return fitted
