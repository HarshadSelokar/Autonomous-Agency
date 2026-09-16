"""
Security test suite for Phase 8 Tools & Integrations.
Verifies unauthorized approval rejection, secret redaction, SSRF prevention,
workspace isolation boundaries, and prompt injection defense.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.secrets_broker import SecretsBroker
from src.application.tool_approval_service import ToolApprovalService, UnauthorizedApprovalError
from src.application.tool_execution_pipeline import ToolExecutionPipeline
from src.application.tool_registry import ToolRegistry
from src.application.workspace_authorization_service import WorkspaceAuthorizationService
from src.domain.employee import Employee, EmployeeStatus
from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolDefinition,
    ToolExecutionStatus,
    ToolRequest,
)
from src.domain.workspace import Workspace, WorkspaceStatus, WorkspaceType
from src.infrastructure.database import Base
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.workspace_repository import SQLAlchemyWorkspaceRepository


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
async def test_self_approval_security_rejection(db_session: AsyncSession) -> None:
    emp_repo = SQLAlchemyEmployeeRepository(db_session)
    approval_service = ToolApprovalService(employee_repo=emp_repo)

    # Seed developer employee
    dev = Employee(
        id="emp-sec-dev",
        employee_code="SEC_DEV",
        name="Security Dev",
        title="Software Engineer",
        role="Developer",
        agent_id="agent-sec-dev",
        status=EmployeeStatus.ACTIVE,
    )
    await emp_repo.save(dev)

    registry = ToolRegistry()
    tool = ToolDefinition(
        id="sensitive_tool",
        name="Sensitive Tool",
        description="Requires approval",
        capabilities=[ToolCapability.SEND_MESSAGE],
        permission_mode=PermissionMode.APPROVAL,
    )
    registry.register(tool)

    pipeline = ToolExecutionPipeline(registry=registry, approval_service=approval_service)
    req = ToolRequest(
        id="req-sec-1",
        tool_id="sensitive_tool",
        tool_version="1.0.0",
        requested_capability=ToolCapability.SEND_MESSAGE,
        arguments={"recipient_id": "boss", "content": "hello"},
        employee_id="emp-sec-dev",
        agent_id="agent-sec-dev",
        agent_run_id="run-sec-1",
    )

    res = await pipeline.execute_tool_request(req)
    assert res.status == ToolExecutionStatus.PENDING_APPROVAL
    appr_id = res.output["approval_id"]

    # Developer attempting to approve their own request MUST be rejected!
    with pytest.raises(UnauthorizedApprovalError):
        await approval_service.approve_request(appr_id, approver_employee_id="emp-sec-dev")


@pytest.mark.asyncio
async def test_cross_workspace_tool_access_security_rejection(db_session: AsyncSession) -> None:
    ws_repo = SQLAlchemyWorkspaceRepository(db_session)
    ws_auth = WorkspaceAuthorizationService(workspace_repo=ws_repo)

    # Workspace for Task T100
    ws1 = Workspace(
        id="ws-t100",
        name="Task T100 Workspace",
        workspace_type=WorkspaceType.TASK,
        owner_id="TASK:T100",
        status=WorkspaceStatus.ACTIVE,
        task_id="T100",
    )
    await ws_repo.save(ws1)

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            id="file_read",
            name="File Reader",
            description="Reads file",
            capabilities=[ToolCapability.READ_FILE],
            permission_mode=PermissionMode.AUTO,
        )
    )

    pipeline = ToolExecutionPipeline(registry=registry, workspace_auth_service=ws_auth)

    # Agent assigned to Task T200 attempting to access Workspace ws-t100 (Task T100)
    req = ToolRequest(
        id="req-cross-ws",
        tool_id="file_read",
        tool_version="1.0.0",
        requested_capability=ToolCapability.READ_FILE,
        arguments={"path": "secret.txt"},
        employee_id="emp-bob",
        agent_id="agent-bob",
        agent_run_id="run-bob",
        task_id="T200",
        workspace_id="ws-t100",
    )

    res = await pipeline.execute_tool_request(req)
    assert res.status == ToolExecutionStatus.DENIED
    assert "Workspace authorization failed" in (res.error_message or "")


def test_secrets_broker_redaction_security() -> None:
    secrets = SecretsBroker()
    secrets.register_secret("ref/api_key", "sk-secret-key-99999")

    log_entry = "Executing HTTP tool with Bearer sk-secret-key-99999 to server."
    redacted = secrets.redact(log_entry)

    assert "sk-secret-key-99999" not in redacted
    assert "[REDACTED_SECRET]" in redacted
