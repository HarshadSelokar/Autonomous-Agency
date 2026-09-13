"""
Integration tests for Memory, Workspace, and Artifact SQLAlchemy Repositories.
"""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.artifact import Artifact, ArtifactStatus, compute_sha256
from src.domain.employee import Employee, EmployeeStatus
from src.domain.memory import (
    MemoryAuthority,
    MemoryEntry,
    MemoryProvenance,
    MemoryScope,
    MemoryStatus,
    MemoryType,
)
from src.domain.workspace import Workspace, WorkspaceStatus, WorkspaceType
from src.infrastructure.database import Base
from src.infrastructure.models.employee_model import employee_domain_to_model
from src.infrastructure.repositories.artifact_repository import SQLAlchemyArtifactRepository
from src.infrastructure.repositories.memory_repository import SQLAlchemyMemoryRepository
from src.infrastructure.repositories.workspace_repository import SQLAlchemyWorkspaceRepository


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_memory_workspace_artifact_repositories(async_session: AsyncSession) -> None:
    # 1. Seed Employee
    emp = Employee(
        id="emp-repo",
        name="Alice Engineer",
        role="Engineer",
        status=EmployeeStatus.ACTIVE,
        employee_code="EMP_REPO",
        title="Senior Dev",
        agent_id="agent-repo",
    )
    async_session.add(employee_domain_to_model(emp))
    await async_session.flush()

    ws_repo = SQLAlchemyWorkspaceRepository(async_session)
    art_repo = SQLAlchemyArtifactRepository(async_session)
    mem_repo = SQLAlchemyMemoryRepository(async_session)

    # 2. Save Workspace
    ws = Workspace(
        id="ws-repo-1",
        name="Task T-100 Workspace",
        workspace_type=WorkspaceType.TASK,
        owner_id="TASK:t-100",
        task_id="t-100",
        status=WorkspaceStatus.ACTIVE,
    )
    saved_ws = await ws_repo.save(ws)
    assert saved_ws.id == "ws-repo-1"

    # 3. Save Artifact
    payload = b"Research Artifact Content"
    checksum = compute_sha256(payload)
    art = Artifact(
        id="art-repo-1",
        workspace_id="ws-repo-1",
        name="research.md",
        mime_type="text/markdown",
        size_bytes=len(payload),
        checksum_sha256=checksum,
        created_by_employee_id="emp-repo",
        storage_key="scratch/research.md",
    )
    saved_art = await art_repo.save(art)
    assert saved_art.id == "art-repo-1"

    # 4. Save MemoryEntry
    mem = MemoryEntry(
        id="mem-repo-1",
        memory_type=MemoryType.SEMANTIC,
        scope=MemoryScope.TASK,
        owner_id="TASK:t-100",
        content="Research Findings for Architecture",
        authority=MemoryAuthority.CONFIRMED,
        confidence=0.9,
        provenance=MemoryProvenance.ARTIFACT,
        artifact_id="art-repo-1",
    )
    saved_mem = await mem_repo.save(mem)
    await async_session.commit()

    assert saved_mem.id == "mem-repo-1"

    # Queries
    fetched_ws = await ws_repo.get_by_id("ws-repo-1")
    assert fetched_ws is not None
    assert fetched_ws.name == "Task T-100 Workspace"

    fetched_arts = await art_repo.list_by_workspace_id("ws-repo-1")
    assert len(fetched_arts) == 1
    assert fetched_arts[0].name == "research.md"

    fetched_mems = await mem_repo.list_by_owner("TASK:t-100")
    assert len(fetched_mems) == 1
    assert fetched_mems[0].content == "Research Findings for Architecture"
