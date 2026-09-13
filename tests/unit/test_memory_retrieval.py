"""
Unit tests for EmbeddingProvider and MemoryRetrievalService hybrid retrieval.
"""

from typing import Any
import pytest

from src.application.embedding_provider import FakeEmbeddingProvider, cosine_similarity
from src.application.memory_retrieval_service import MemoryRetrievalService
from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryScope,
    MemoryStatus,
    MemoryType,
)
from tests.unit.test_memory_service import MemoryMemoryRepository


@pytest.mark.asyncio
async def test_fake_embedding_provider_and_cosine_similarity() -> None:
    provider = FakeEmbeddingProvider(dimension=64)
    v1 = await provider.embed("PostgreSQL database")
    v2 = await provider.embed("PostgreSQL database")
    v3 = await provider.embed("Unrelated cooking recipe")

    assert len(v1) == 64
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)
    assert cosine_similarity(v1, v3) < 0.95


@pytest.mark.asyncio
async def test_hybrid_memory_retrieval_ranking() -> None:
    repo = MemoryMemoryRepository()
    provider = FakeEmbeddingProvider()
    retrieval_service = MemoryRetrievalService(memory_repo=repo, embedding_provider=provider)

    vec_db = await provider.embed("PostgreSQL primary database configuration")
    vec_frontend = await provider.embed("React frontend architecture")

    m1 = MemoryEntry(
        id="mem-1",
        memory_type=MemoryType.ORGANIZATIONAL,
        scope=MemoryScope.COMPANY,
        owner_id="COMPANY",
        content="PostgreSQL primary database configuration",
        authority=MemoryAuthority.AUTHORITATIVE,
        confidence=1.0,
        embedding=vec_db,
    )
    m2 = MemoryEntry(
        id="mem-2",
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.TASK,
        owner_id="TASK:t-1",
        content="React frontend component hierarchy",
        authority=MemoryAuthority.GENERATED,
        confidence=0.5,
        embedding=vec_frontend,
    )
    await repo.save(m1)
    await repo.save(m2)

    # Retrieval for database query should rank m1 higher due to both similarity & AUTHORITATIVE status
    results = await retrieval_service.retrieve_memories(
        query="PostgreSQL database", owner_ids=["TASK:t-1"], limit=5
    )
    assert len(results) == 2
    assert results[0]["memory"].id == "mem-1"
    assert results[0]["score"] > results[1]["score"]
