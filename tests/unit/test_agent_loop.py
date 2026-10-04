"""Unit tests for the multi-step agent loop and provider tool-call mapping."""

import json
from typing import Any

import httpx
import pytest

from src.application.agent_loop import AgentLoop, ToolOutcome
from src.application.provider_registry import ModelProviderRegistry
from src.application.retry import RetryPolicy
from src.domain.exceptions import CancellationError
from src.domain.model_provider import ChatMessage, ModelRequest
from src.infrastructure.models.fake_provider import FakeModelProvider
from src.infrastructure.providers.openai_compatible_provider import OpenAICompatibleModelProvider
from src.infrastructure.providers.openai_format import messages_to_payload, parse_tool_calls


class RecordingToolbox:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.fail = fail

    def specs(self) -> list[dict[str, Any]]:
        return [{"name": "echo", "description": "Echo text", "parameters": {"type": "object"}}]

    def describe(self, name: str, arguments: dict[str, Any]) -> str:
        return f"echoing {arguments.get('text', '')}"

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        self.calls.append((name, arguments))
        if self.fail:
            raise RuntimeError("tool exploded")
        return ToolOutcome(content=f"echo: {arguments.get('text', '')}")


def make_loop(provider: FakeModelProvider, max_steps: int = 10) -> AgentLoop:
    registry = ModelProviderRegistry()
    registry.register(provider)
    return AgentLoop(provider_registry=registry, retry_policy=RetryPolicy(max_retries=0), max_steps=max_steps)


async def run(loop: AgentLoop, toolbox: RecordingToolbox, **kwargs: Any):
    return await loop.run(
        provider="fake", model="fake", system_prompt="sys", user_prompt="do it", toolbox=toolbox, **kwargs
    )


async def test_loop_executes_tools_then_returns_final_answer():
    provider = FakeModelProvider()
    provider.script(tool_calls=[{"id": "c1", "name": "echo", "arguments": {"text": "one"}}])
    provider.script(tool_calls=[{"id": "c2", "name": "echo", "arguments": {"text": "two"}}])
    provider.script(content="all done")
    toolbox = RecordingToolbox()
    events: list[dict[str, Any]] = []

    async def sink(event: dict[str, Any]) -> None:
        events.append(event)

    result = await run(make_loop(provider), toolbox, on_event=sink)

    assert result.completed
    assert result.final_text == "all done"
    assert result.steps == 3
    assert result.tool_calls == 2
    assert toolbox.calls == [("echo", {"text": "one"}), ("echo", {"text": "two"})]
    assert result.usage["total_tokens"] == 90  # three calls at 30 tokens each

    # The model must see its own tool call and the tool's result on the next turn
    second_request = provider.requests[1]
    assert second_request.messages[-2].tool_calls[0]["id"] == "c1"
    assert second_request.messages[-1].role == "tool"
    assert second_request.messages[-1].tool_call_id == "c1"
    assert second_request.messages[-1].content == "echo: one"
    assert second_request.tools[0]["name"] == "echo"

    assert [e["summary"] for e in events if e["type"] == "tool_call"] == ["echoing one", "echoing two"]
    assert events[-1]["type"] == "final"


async def test_loop_stops_at_step_limit():
    provider = FakeModelProvider()
    for i in range(5):
        provider.script(tool_calls=[{"id": f"c{i}", "name": "echo", "arguments": {}}])

    result = await run(make_loop(provider, max_steps=3), RecordingToolbox())

    assert result.stop_reason == "max_steps"
    assert not result.completed
    assert result.steps == 3


async def test_tool_exception_is_reported_to_model_not_raised():
    provider = FakeModelProvider()
    provider.script(tool_calls=[{"id": "c1", "name": "echo", "arguments": {}}])
    provider.script(content="recovered")

    result = await run(make_loop(provider), RecordingToolbox(fail=True))

    assert result.completed
    assert "tool exploded" in provider.requests[1].messages[-1].content


async def test_loop_honours_cancellation():
    provider = FakeModelProvider()
    provider.script(content="never reached")

    with pytest.raises(CancellationError):
        await run(make_loop(provider), RecordingToolbox(), should_cancel=lambda: True)
    assert provider.call_count == 0


async def test_final_tool_call_ends_the_run_with_structured_payload():
    provider = FakeModelProvider()
    provider.script(tool_calls=[{"id": "c1", "name": "echo", "arguments": {"text": "look"}}])
    provider.script(tool_calls=[{"id": "c2", "name": "submit", "arguments": {"approved": True}}])
    toolbox = RecordingToolbox()
    final_tool = {"name": "submit", "description": "Submit", "parameters": {"type": "object"}}

    result = await run(make_loop(provider), toolbox, final_tool=final_tool)

    assert result.completed
    assert result.final_payload == {"approved": True}
    assert toolbox.calls == [("echo", {"text": "look"})]  # the final tool is not sent to the toolbox
    assert [t["name"] for t in provider.requests[0].tools] == ["echo", "submit"]


async def test_rejected_tool_call_is_fed_back_to_the_model():
    from src.domain.exceptions import ModelExecutionError

    class RejectingOnce(FakeModelProvider):
        async def generate(self, request: ModelRequest):
            if self.call_count == 0:
                self.call_count += 1
                self.requests.append(request)
                raise ModelExecutionError("Groq API error (400): Tool call validation failed: tool 'json' not in request.tools")
            return await super().generate(request)

    provider = RejectingOnce()
    provider.script(content="answered in text instead")

    result = await run(make_loop(provider), RecordingToolbox())

    assert result.completed and result.final_text == "answered in text instead"
    correction = provider.requests[1].messages[-1]
    assert correction.role == "user"
    assert "rejected by the API" in correction.content and "echo" in correction.content


async def test_other_model_errors_are_not_swallowed():
    from src.domain.exceptions import ModelExecutionError

    provider = FakeModelProvider(should_fail_with=ModelExecutionError("Groq API error (400): bad request"))
    with pytest.raises(ModelExecutionError):
        await run(make_loop(provider), RecordingToolbox())


def test_context_fitting_elides_oldest_tool_output_only():
    loop = AgentLoop(provider_registry=ModelProviderRegistry(), max_context_chars=1000)
    messages = [ChatMessage(role="system", content="s"), ChatMessage(role="user", content="u")]
    for i in range(6):
        messages.append(ChatMessage(role="tool", content="x" * 400, tool_call_id=f"c{i}"))

    fitted = loop._fit_context(messages)

    assert fitted[2].content.startswith("[earlier tool output elided")
    assert fitted[2].tool_call_id == "c0"
    assert [m.content for m in fitted[-4:]] == ["x" * 400] * 4  # most recent results stay intact
    assert messages[2].content == "x" * 400  # the transcript itself is not mutated


def test_openai_message_mapping_round_trip():
    payload = messages_to_payload(
        [
            ChatMessage(role="user", content="hi"),
            ChatMessage(role="assistant", content="", tool_calls=[{"id": "c1", "name": "f", "arguments": {"a": 1}}]),
            ChatMessage(role="tool", content="result", tool_call_id="c1"),
        ]
    )
    assert payload[1]["tool_calls"][0]["function"] == {"name": "f", "arguments": '{"a": 1}'}
    assert payload[2] == {"role": "tool", "tool_call_id": "c1", "content": "result"}

    assert parse_tool_calls(payload[1]["tool_calls"]) == [{"id": "c1", "name": "f", "arguments": {"a": 1}}]
    malformed = parse_tool_calls([{"id": "c2", "function": {"name": "f", "arguments": "{not json"}}])
    assert malformed[0]["arguments"] == {"_malformed_arguments": "{not json"}


async def test_openai_compatible_provider_sends_tools_and_parses_calls():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "resp-1",
                "model": "test-model",
                "choices": [
                    {
                        "finish_reason": "tool_calls",
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {"id": "c9", "type": "function", "function": {"name": "echo", "arguments": '{"text": "x"}'}}
                            ],
                        },
                    }
                ],
                "usage": {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12},
            },
        )

    provider = OpenAICompatibleModelProvider(
        api_key="k", base_url="https://llm.example/v1/", default_model="test-model",
        transport=httpx.MockTransport(handler),
    )
    response = await provider.generate(
        ModelRequest(
            model="",
            messages=[ChatMessage(role="user", content="hi")],
            tools=[{"name": "echo", "description": "d", "parameters": {"type": "object"}}],
        )
    )

    assert seen["url"] == "https://llm.example/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
    assert seen["body"]["model"] == "test-model"
    assert seen["body"]["tools"][0]["function"]["name"] == "echo"
    assert response.tool_calls == [{"id": "c9", "name": "echo", "arguments": {"text": "x"}}]
    assert response.content == ""
    assert response.usage.total_tokens == 12
