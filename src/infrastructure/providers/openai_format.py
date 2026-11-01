"""
Shared mapping between the provider-neutral chat structures and the OpenAI-style
chat-completions wire format (used by Groq, OpenAI and OpenAI-compatible gateways).
"""

import json
from typing import Any

from src.domain.model_provider import ChatMessage


def messages_to_payload(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for msg in messages:
        if msg.role == "tool":
            payload.append(
                {"role": "tool", "tool_call_id": msg.tool_call_id or "", "content": msg.content}
            )
            continue

        item: dict[str, Any] = {"role": msg.role, "content": msg.content}
        if msg.name:
            item["name"] = msg.name
        if msg.tool_calls:
            item["tool_calls"] = [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(call.get("arguments") or {}),
                    },
                }
                for call in msg.tool_calls
            ]
        payload.append(item)
    return payload


def tools_to_payload(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Accepts neutral specs {"name", "description", "parameters"} and wraps them as functions."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
            },
        }
        for tool in tools
    ]


def parse_tool_calls(raw_calls: Any) -> list[dict[str, Any]]:
    """Normalize SDK objects or raw dicts into [{"id", "name", "arguments": dict}]."""
    normalized: list[dict[str, Any]] = []
    for index, call in enumerate(raw_calls or []):
        function = call.get("function") if isinstance(call, dict) else getattr(call, "function", None)
        if function is None:
            continue
        if isinstance(function, dict):
            name, raw_args = function.get("name", ""), function.get("arguments")
        else:
            name, raw_args = getattr(function, "name", ""), getattr(function, "arguments", None)
        call_id = call.get("id") if isinstance(call, dict) else getattr(call, "id", None)

        arguments: dict[str, Any]
        if isinstance(raw_args, dict):
            arguments = raw_args
        else:
            try:
                parsed = json.loads(raw_args) if raw_args else {}
                arguments = parsed if isinstance(parsed, dict) else {"value": parsed}
            except (TypeError, json.JSONDecodeError):
                # Surface the malformed payload to the caller instead of dropping the call
                arguments = {"_malformed_arguments": str(raw_args)}

        normalized.append({"id": call_id or f"call_{index}", "name": name, "arguments": arguments})
    return normalized
