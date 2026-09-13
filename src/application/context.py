"""
Structured Agent Context Subsystem.
Assembles structured runtime context from Agent identity, role, objective, policies,
and reference data into provider-neutral ChatMessages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.domain.agent import Agent
from src.domain.model_provider import ChatMessage


class ContextSource(str, Enum):
    SYSTEM = "system"
    AGENT_IDENTITY = "agent_identity"
    ROLE_INSTRUCTIONS = "role_instructions"
    OBJECTIVE = "objective"
    CONSTRAINTS = "constraints"
    POLICIES = "policies"
    REFERENCE_DATA = "reference_data"


@dataclass
class ContextItem:
    source: ContextSource
    content: str
    priority: int = 10  # Lower number = higher priority
    metadata: dict[str, Any] = field(default_factory=dict)


class ContextProvider(ABC):
    """Abstract interface for external/internal context providers."""

    @abstractmethod
    async def get_context_items(self, agent: Agent, objective: str) -> list[ContextItem]:
        """Fetch additional context items relevant to the agent and objective."""
        pass


class StaticContextProvider(ContextProvider):
    """Simple context provider injecting fixed reference data items."""

    def __init__(self, items: list[ContextItem] | None = None) -> None:
        self.items = items or []

    async def get_context_items(self, agent: Agent, objective: str) -> list[ContextItem]:
        return self.items


@dataclass
class AgentExecutionContext:
    agent: Agent
    objective: str
    task_id: str | None = None
    items: list[ContextItem] = field(default_factory=list)
    response_schema: dict[str, Any] | None = None

    def to_chat_messages(self) -> list[ChatMessage]:
        """
        Render structured context items into a sequence of ChatMessage objects
        suited for model consumption.
        """
        sorted_items = sorted(self.items, key=lambda x: x.priority)
        system_sections: list[str] = []

        for item in sorted_items:
            if item.source in (
                ContextSource.SYSTEM,
                ContextSource.AGENT_IDENTITY,
                ContextSource.ROLE_INSTRUCTIONS,
                ContextSource.CONSTRAINTS,
                ContextSource.POLICIES,
            ):
                system_sections.append(item.content)

        system_prompt = "\n\n".join(system_sections)
        messages = [ChatMessage(role="system", content=system_prompt)]

        # Add reference data if available
        for item in sorted_items:
            if item.source == ContextSource.REFERENCE_DATA:
                ref_name = item.metadata.get("name", "Info")
                messages.append(
                    ChatMessage(
                        role="user",
                        content=f"[REFERENCE CONTEXT ({ref_name})]\n{item.content}",
                    )
                )

        # Add main objective message
        for item in sorted_items:
            if item.source == ContextSource.OBJECTIVE:
                messages.append(ChatMessage(role="user", content=item.content))

        return messages


class ContextBuilder:
    """Assembles structured AgentExecutionContext objects."""

    def __init__(self, providers: list[ContextProvider] | None = None) -> None:
        self.providers = providers or []

    def add_provider(self, provider: ContextProvider) -> None:
        self.providers.append(provider)

    async def build(
        self,
        agent: Agent,
        objective: str,
        task_id: str | None = None,
        extra_items: list[ContextItem] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> AgentExecutionContext:
        items: list[ContextItem] = []

        # 1. System Runtime Prompt
        items.append(
            ContextItem(
                source=ContextSource.SYSTEM,
                content=(
                    "You are an AI Employee operating within an Autonomous AI Organization. "
                    "Execute your assigned objective accurately, following all permissions, "
                    "policies, and architectural constraints."
                ),
                priority=1,
            )
        )

        # 2. Agent Identity & Description
        identity_text = (
            f"AGENT IDENTITY:\n"
            f"- Agent ID: {agent.id}\n"
            f"- Name: {agent.name}\n"
            f"- Role: {agent.role}\n"
            f"- Description: {agent.description}"
        )
        items.append(
            ContextItem(
                source=ContextSource.AGENT_IDENTITY,
                content=identity_text,
                priority=2,
            )
        )

        # 3. Role Instructions (Responsibilities & Capabilities)
        resp_formatted = (
            "\n".join(f"  * {r}" for r in agent.responsibilities)
            if agent.responsibilities
            else "  * Standard employee duties"
        )
        cap_list = ", ".join(agent.capabilities) or "general"
        role_text = (
            f"ROLE RESPONSIBILITIES & CAPABILITIES:\n"
            f"Responsibilities:\n{resp_formatted}\n"
            f"Capabilities: {cap_list}"
        )
        items.append(
            ContextItem(
                source=ContextSource.ROLE_INSTRUCTIONS,
                content=role_text,
                priority=3,
            )
        )

        # 4. Constraints & Permissions
        perms = ", ".join(agent.permission_profile.permissions) or "none"
        constraints_text = f"CONSTRAINTS & PERMISSIONS:\n- Granted Permissions: {perms}"
        items.append(
            ContextItem(
                source=ContextSource.CONSTRAINTS,
                content=constraints_text,
                priority=4,
            )
        )

        # 5. Policies
        policies_text = (
            f"ORGANIZATIONAL POLICIES:\n"
            f"- Verification Required: {agent.verification_policy.required}\n"
            f"- Verifier Role: {agent.verification_policy.verifier_role or 'N/A'}"
        )
        items.append(
            ContextItem(
                source=ContextSource.POLICIES,
                content=policies_text,
                priority=5,
            )
        )

        # 6. Objective Item
        items.append(
            ContextItem(
                source=ContextSource.OBJECTIVE,
                content=f"ASSIGNED OBJECTIVE:\n{objective}",
                priority=100,
            )
        )

        # 7. Collect from external ContextProviders
        for provider in self.providers:
            provider_items = await provider.get_context_items(agent, objective)
            items.extend(provider_items)

        # 8. Add extra custom items passed to builder
        if extra_items:
            items.extend(extra_items)

        return AgentExecutionContext(
            agent=agent,
            objective=objective,
            task_id=task_id,
            items=items,
            response_schema=response_schema,
        )


class ToolContextProvider(ContextProvider):
    """Injects sanitized tool definitions and execution capabilities into Agent context."""

    def __init__(self, registry: Any) -> None:
        self.registry = registry

    async def get_context_items(self, agent: Agent, objective: str) -> list[ContextItem]:
        safe_tools = self.registry.get_safe_metadata_for_agent()
        if not safe_tools:
            return []

        formatted_tools: list[str] = []
        for t in safe_tools:
            formatted_tools.append(
                f" - Tool ID: {t['tool_id']} (v{t['version']}) | Risk: {t['risk_level']} | Mode: {t['permission_mode']}\n"
                f"   Description: {t['description']}\n"
                f"   Capabilities: {', '.join(t['capabilities'])}\n"
                f"   Input Schema: {t['input_schema']}"
            )

        content_text = (
            "AVAILABLE ORGANIZATIONAL TOOLS & CAPABILITIES:\n"
            "To request a tool execution, output a structured tool request block in JSON:\n"
            '{"tool_request": {"tool_id": "<ID>", "capability": "<CAPABILITY>", "arguments": {...}}}\n'
            "Backend controls tool authorization, workspace boundaries, policies, and approvals.\n\n"
            + "\n".join(formatted_tools)
        )

        return [
            ContextItem(
                source=ContextSource.REFERENCE_DATA,
                content=content_text,
                priority=10,
                metadata={"name": "Available Tools"},
            )
        ]

