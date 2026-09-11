"""
Unit tests for Agent Context Builder and Context Subsystem.
"""

import pytest

from src.application.context import (
    ContextBuilder,
    ContextItem,
    ContextSource,
    StaticContextProvider,
)
from src.domain.agent import Agent, PermissionProfile, VerificationPolicy


@pytest.mark.asyncio
async def test_context_builder_builds_structured_context() -> None:
    agent = Agent(
        id="researcher_01",
        name="Research Bot",
        role="Researcher",
        description="Performs tech research",
        responsibilities=["Investigate frameworks"],
        capabilities=["research"],
        permission_profile=PermissionProfile(permissions=["read_repo"]),
        verification_policy=VerificationPolicy(required=True, verifier_role="Lead"),
    )

    builder = ContextBuilder()
    context = await builder.build(
        agent=agent,
        objective="Explain PostgreSQL benefits",
    )

    assert context.agent.id == "researcher_01"
    assert context.objective == "Explain PostgreSQL benefits"
    assert len(context.items) >= 6

    messages = context.to_chat_messages()
    assert len(messages) == 2  # System message + User objective message
    assert messages[0].role == "system"
    assert "Research Bot" in messages[0].content
    assert "read_repo" in messages[0].content
    assert messages[1].role == "user"
    assert "Explain PostgreSQL benefits" in messages[1].content


@pytest.mark.asyncio
async def test_context_builder_with_providers_and_extra_items() -> None:
    agent = Agent(id="ag_02", name="Dev Bot", role="Developer")

    ref_provider = StaticContextProvider(
        items=[
            ContextItem(
                source=ContextSource.REFERENCE_DATA,
                content="SQLAlchemy 2.0 is an async ORM.",
                priority=10,
                metadata={"name": "ORM Spec"},
            )
        ]
    )

    builder = ContextBuilder(providers=[ref_provider])
    context = await builder.build(
        agent=agent,
        objective="Write SQLAlchemy code",
        extra_items=[
            ContextItem(
                source=ContextSource.REFERENCE_DATA,
                content="FastAPI is an async framework.",
                priority=11,
                metadata={"name": "API Spec"},
            )
        ],
    )

    messages = context.to_chat_messages()
    assert len(messages) == 4  # System + 2 Reference + User Objective
    assert messages[1].role == "user"
    assert "SQLAlchemy 2.0" in messages[1].content
    assert messages[2].role == "user"
    assert "FastAPI" in messages[2].content
