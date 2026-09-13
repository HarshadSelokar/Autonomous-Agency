"""
Unit tests for MemoryContextBuilder and prompt security framing.
"""

from typing import Any
import pytest

from src.application.embedding_provider import FakeEmbeddingProvider
from src.application.memory_context_builder import MemoryContextBuilder
from src.application.memory_retrieval_service import MemoryRetrievalService
from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryScope,
    MemoryType,
)
from tests.unit.test_memory_service import MemoryMemoryRepository


@pytest.mark.asyncio
async def test_memory_context_builder_framing_and_priority() -> None:
    repo = MemoryMemoryRepository()
    provider = FakeEmbeddingProvider()
    retrieval_service = MemoryRetrievalService(memory_repo=repo, embedding_provider=provider)
    builder = MemoryContextBuilder(retrieval_service=retrieval_service)

    m1 = MemoryEntry(
        id="mem-1",
        memory_type=MemoryType.ORGANIZATIONAL,
        scope=MemoryScope.COMPANY,
        owner_id="COMPANY",
        content="Official Database Policy: PostgreSQL is required.",
        authority=MemoryAuthority.AUTHORITATIVE,
        confidence=1.0,
    )
    m2 = MemoryEntry(
        id="mem-2",
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.TASK,
        owner_id="TASK:t-100",
        content="Observation: JWT token expiration is set to 3600s.",
        authority=MemoryAuthority.CONFIRMED,
        confidence=0.9,
    )
    await repo.save(m1)
    await repo.save(m2)

    context = await builder.build_context(
        task_id="t-100", requesting_employee_id="emp-1", query="database policy"
    )

    assert context["task_id"] == "t-100"
    assert context["memory_count"] == 2
    framed = context["framed_prompt_context"]
    assert "=== BEGIN UNTRUSTED ORGANIZATIONAL MEMORY CONTEXT" in framed
    assert "=== END UNTRUSTED ORGANIZATIONAL MEMORY CONTEXT ===" in framed
    assert "Official Database Policy: PostgreSQL is required." in framed
