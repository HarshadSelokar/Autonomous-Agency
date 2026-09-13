"""
Failure injection and resilience tests for Phase 7 Memory, Workspace, and Artifact systems.
"""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.embedding_provider import EmbeddingProviderInterface
from src.application.memory_retrieval_service import MemoryRetrievalService
from src.application.memory_service import MemoryService
from src.domain.artifact import Artifact, compute_sha256
from src.domain.memory import MemoryAuthority, MemoryEntry, MemoryProvenance, MemoryScope, MemoryType
from src.infrastructure.database import Base
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.memory_repository import SQLAlchemyMemoryRepository
from src.infrastructure.storage_provider import LocalStorageProvider


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


class FailingEmbeddingProvider(EmbeddingProviderInterface):
    async def embed(self, text: str) -> list[float]:
        raise RuntimeError("External Embedding API connection timed out!")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("External Embedding API connection timed out!")


@pytest.mark.asyncio
async def test_embedding_provider_failure_resilience(db_session: AsyncSession) -> None:
    mem_repo = SQLAlchemyMemoryRepository(db_session)
    emp_repo = SQLAlchemyEmployeeRepository(db_session)
    failing_provider = FailingEmbeddingProvider()

    service = MemoryService(memory_repo=mem_repo, employee_repo=emp_repo)
    retrieval_service = MemoryRetrievalService(memory_repo=mem_repo, embedding_provider=failing_provider)

    # 1. Memory creation succeeds without failing when embedding fails
    entry = await service.create_memory(
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.COMPANY,
        owner_id="COMPANY",
        content="Resilience knowledge entry.",
        authority=MemoryAuthority.CONFIRMED,
        provenance=MemoryProvenance.MESSAGE,
    )
    assert entry.id is not None

    # 2. Retrieval gracefully falls back to structured metadata filtering
    results = await retrieval_service.retrieve_memories(
        query="resilience",
        owner_ids=["COMPANY"],
    )
    assert len(results) >= 1
    assert results[0]["memory"].id == entry.id


@pytest.mark.asyncio
async def test_storage_provider_read_missing_key_failure() -> None:
    storage = LocalStorageProvider(base_dir="scratch/test_storage_failure")
    with pytest.raises(FileNotFoundError):
        await storage.read_bytes("non_existent_key_12345")


@pytest.mark.asyncio
async def test_artifact_version_progression_integrity() -> None:
    art_v1 = Artifact(
        id="art-1",
        workspace_id="ws-1",
        name="doc.txt",
        mime_type="text/plain",
        size_bytes=10,
        checksum_sha256="hash1",
        created_by_employee_id="emp-1",
        version=1,
        storage_key="key1",
    )

    content_v2 = b"Updated content"
    checksum_v2 = compute_sha256(content_v2)

    art_v2 = art_v1.create_next_version(
        new_artifact_id="art-2",
        size_bytes=len(content_v2),
        checksum_sha256=checksum_v2,
        storage_key="key2",
        creator_employee_id="emp-1",
    )

    assert art_v1.status.value == "SUPERSEDED"
    assert art_v2.status.value == "ACTIVE"
    assert art_v2.version == 2
    assert art_v2.checksum_sha256 == checksum_v2
