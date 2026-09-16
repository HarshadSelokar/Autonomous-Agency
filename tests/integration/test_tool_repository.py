"""
Integration tests for Tool, ToolExecution, and ToolApproval SQLAlchemy Repositories.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.tool import (
    ApprovalStatus,
    PermissionMode,
    ToolApproval,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolExecution,
    ToolExecutionStatus,
)
from src.infrastructure.database import Base
from src.infrastructure.repositories.tool_repository import (
    SQLAlchemyToolApprovalRepository,
    SQLAlchemyToolExecutionRepository,
    SQLAlchemyToolRepository,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_tool_repository_crud(db_session: AsyncSession) -> None:
    repo = SQLAlchemyToolRepository(db_session)
    tool = ToolDefinition(
        id="file_read_repo_test",
        name="File Reader",
        description="Reads workspace files",
        category=ToolCategory.FILESYSTEM,
        capabilities=[ToolCapability.READ_FILE],
        permission_mode=PermissionMode.AUTO,
    )
    saved = await repo.save(tool)
    assert saved.id == "file_read_repo_test"

    retrieved = await repo.get_by_id("file_read_repo_test")
    assert retrieved is not None
    assert retrieved.name == "File Reader"
    assert retrieved.supports_capability(ToolCapability.READ_FILE)


@pytest.mark.asyncio
async def test_tool_execution_and_approval_repository(db_session: AsyncSession) -> None:
    exec_repo = SQLAlchemyToolExecutionRepository(db_session)
    appr_repo = SQLAlchemyToolApprovalRepository(db_session)

    # 1. Save Execution
    execution = ToolExecution(
        id="exec-db-1",
        request_id="req-db-1",
        tool_id="send_msg",
        tool_version="1.0.0",
        capability=ToolCapability.SEND_MESSAGE,
        actor_employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
        status=ToolExecutionStatus.PENDING_APPROVAL,
    )
    saved_exec = await exec_repo.save(execution)
    assert saved_exec.id == "exec-db-1"

    # 2. Save Approval
    approval = ToolApproval(
        id="appr-db-1",
        execution_id="exec-db-1",
        tool_id="send_msg",
        capability=ToolCapability.SEND_MESSAGE,
        requester_employee_id="emp-1",
    )
    saved_appr = await appr_repo.save(approval)
    assert saved_appr.id == "appr-db-1"

    retrieved_appr = await appr_repo.get_by_id("appr-db-1")
    assert retrieved_appr is not None
    assert retrieved_appr.status == ApprovalStatus.PENDING
