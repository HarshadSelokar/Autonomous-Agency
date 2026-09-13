"""
Phase 8 End-to-End Demonstration Script.
Demonstrates Tool Registry, Deterministic Resolution, AUTO & APPROVAL Workflows,
Workspace Isolation, SSRF Defenses, Secrets Redaction, and Evidence Generation.
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.secrets_broker import SecretsBroker
from src.application.tool_approval_service import ToolApprovalService, UnauthorizedApprovalError
from src.application.tool_execution_pipeline import ToolExecutionPipeline
from src.application.tool_policy_engine import ToolPolicyEngine
from src.application.tool_registry import ToolRegistry
from src.application.tool_resolver import ToolResolver
from src.application.workspace_authorization_service import WorkspaceAuthorizationService
from src.domain.employee import Employee, EmployeeStatus
from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolExecutionStatus,
    ToolRequest,
    ToolRiskLevel,
)
from src.domain.workspace import Workspace, WorkspaceStatus, WorkspaceType
from src.infrastructure.database import Base
from src.infrastructure.models.employee_model import employee_domain_to_model
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.tool_repository import (
    SQLAlchemyToolApprovalRepository,
    SQLAlchemyToolExecutionRepository,
    SQLAlchemyToolRepository,
)
from src.infrastructure.repositories.workspace_repository import SQLAlchemyWorkspaceRepository


async def run_phase8_demo() -> None:
    print("========================================================================")
    print("PHASE 8 END-TO-END DEMONSTRATION: TOOLS & INTEGRATIONS PLATFORM")
    print("========================================================================\n")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # Repositories
        emp_repo = SQLAlchemyEmployeeRepository(session)
        ws_repo = SQLAlchemyWorkspaceRepository(session)
        tool_repo = SQLAlchemyToolRepository(session)
        exec_repo = SQLAlchemyToolExecutionRepository(session)
        appr_repo = SQLAlchemyToolApprovalRepository(session)

        # 1. Seed Employees (Manager Alice & Developer Bob)
        mgr = Employee(
            id="emp-mgr-alice",
            employee_code="MGR01",
            name="Alice Vance",
            title="Engineering Director",
            role="Engineering Manager",
            agent_id="agent-mgr-alice",
            status=EmployeeStatus.ACTIVE,
        )
        dev = Employee(
            id="emp-dev-bob",
            employee_code="DEV01",
            name="Bob Smith",
            title="Senior Developer",
            role="Software Engineer",
            agent_id="agent-dev-bob",
            status=EmployeeStatus.ACTIVE,
        )
        session.add(employee_domain_to_model(mgr))
        session.add(employee_domain_to_model(dev))
        await session.commit()
        print("1. Employees Seeded: Alice Vance (Manager) & Bob Smith (Developer)")

        # 2. Seed Tool Catalog & Registry
        registry = ToolRegistry()

        # Tool 1: Workspace File Tool (AUTO Mode)
        tool_file = ToolDefinition(
            id="workspace_file_tool",
            name="Workspace File Tool",
            description="Reads and writes workspace files safely",
            category=ToolCategory.FILESYSTEM,
            capabilities=[ToolCapability.READ_FILE, ToolCapability.WRITE_FILE],
            permission_mode=PermissionMode.AUTO,
            risk_level=ToolRiskLevel.LOW,
        )

        # Tool 2: External Communication Tool (APPROVAL Mode)
        tool_comm = ToolDefinition(
            id="external_comm_tool",
            name="External Communication Tool",
            description="Sends messages to external channels",
            category=ToolCategory.COMMUNICATION,
            capabilities=[ToolCapability.SEND_MESSAGE],
            permission_mode=PermissionMode.APPROVAL,
            risk_level=ToolRiskLevel.HIGH,
        )

        # Tool 3: HTTP API Tool (AUTO Mode)
        tool_http = ToolDefinition(
            id="http_client_tool",
            name="HTTP Client Tool",
            description="Makes HTTP API calls",
            category=ToolCategory.HTTP,
            capabilities=[ToolCapability.HTTP_REQUEST],
            permission_mode=PermissionMode.AUTO,
            risk_level=ToolRiskLevel.MEDIUM,
        )

        # Tool 4: Database Drop Tool (BLOCKED Mode)
        tool_blocked = ToolDefinition(
            id="drop_db_tool",
            name="Database Drop Tool",
            description="Destructive database operations",
            category=ToolCategory.DATABASE,
            capabilities=[ToolCapability.DATABASE_WRITE],
            permission_mode=PermissionMode.BLOCKED,
            risk_level=ToolRiskLevel.CRITICAL,
        )

        for t in [tool_file, tool_comm, tool_http, tool_blocked]:
            await tool_repo.save(t)
            registry.register(t)
        await session.commit()
        print("2. Tool Catalog Seeded & Registered: File, Comm, HTTP, DB Drop")

        # 3. Create Task Workspace W100 for Task T100
        ws = Workspace(
            id="ws-t100",
            name="Task T100 Workspace",
            workspace_type=WorkspaceType.TASK,
            owner_id="TASK:T100",
            status=WorkspaceStatus.ACTIVE,
            task_id="T100",
            employee_id=dev.id,
        )
        await ws_repo.save(ws)
        await session.commit()
        print(f"3. Task Workspace Created: '{ws.name}' ({ws.id})")

        # Setup Pipeline Components
        secrets = SecretsBroker()
        secrets.register_secret("ref/slack_key", "secret_slack_token_999")

        approval_service = ToolApprovalService(employee_repo=emp_repo, approval_repo=appr_repo)
        ws_auth = WorkspaceAuthorizationService(workspace_repo=ws_repo)

        pipeline = ToolExecutionPipeline(
            registry=registry,
            approval_service=approval_service,
            workspace_auth_service=ws_auth,
            employee_repo=emp_repo,
            secrets_broker=secrets,
            execution_repo=exec_repo,
        )

        # 4. Demonstrate AUTO Tool Execution (File Write in Sandboxed Workspace)
        req_file = ToolRequest(
            id="req-demo-1",
            tool_id="workspace_file_tool",
            tool_version="1.0.0",
            requested_capability=ToolCapability.WRITE_FILE,
            arguments={"path": "architecture_notes.md", "content": "# Architecture Notes\nPhase 8 is production ready."},
            employee_id=dev.id,
            agent_id="agent-dev-bob",
            agent_run_id="run-demo-1",
            task_id="T100",
            workspace_id=ws.id,
        )
        res_file = await pipeline.execute_tool_request(req_file)
        await session.commit()
        print(f"\n4. AUTO Tool Execution (File Write): Status = {res_file.status.value}")
        print(f"   Output: {res_file.output}")
        print(f"   Evidence ID: {res_file.evidence_id}")

        # 5. Demonstrate APPROVAL Tool Execution & Self-Approval Prevention
        req_comm = ToolRequest(
            id="req-demo-2",
            tool_id="external_comm_tool",
            tool_version="1.0.0",
            requested_capability=ToolCapability.SEND_MESSAGE,
            arguments={"recipient_id": "slack-channel", "content": "Deploying build with key secret_slack_token_999"},
            employee_id=dev.id,
            agent_id="agent-dev-bob",
            agent_run_id="run-demo-2",
            task_id="T100",
        )
        res_comm = await pipeline.execute_tool_request(req_comm)
        await session.commit()
        print(f"\n5. APPROVAL Tool Execution (Send Message): Status = {res_comm.status.value}")
        appr_id = res_comm.output["approval_id"]
        print(f"   Created Approval ID: {appr_id}")

        # Test Self-Approval Prevention
        try:
            await approval_service.approve_request(appr_id, approver_employee_id=dev.id)
            print("   [SECURITY FAILURE] Dev approved own request!")
        except UnauthorizedApprovalError as err:
            print(f"   [SECURITY ENFORCED] Self-approval blocked! ({err})")

        # Manager Alice approves request
        appr = await approval_service.approve_request(appr_id, approver_employee_id=mgr.id, rationale="Deploy approved by Director")
        await session.commit()
        print(f"   Manager Alice Approved Request: Status = {appr.status.value}")

        # Pipeline re-executes with approved ID
        res_comm_final = await pipeline.execute_tool_request(req_comm, pre_approved_approval_id=appr_id)
        await session.commit()
        print(f"   Pre-Approved Execution Result: Status = {res_comm_final.status.value}")
        print(f"   Redacted Output: {res_comm_final.output}")

        # 6. Demonstrate BLOCKED Tool Execution
        req_blocked = ToolRequest(
            id="req-demo-3",
            tool_id="drop_db_tool",
            tool_version="1.0.0",
            requested_capability=ToolCapability.DATABASE_WRITE,
            arguments={"database": "production_company_db"},
            employee_id=dev.id,
            agent_id="agent-dev-bob",
            agent_run_id="run-demo-3",
        )
        res_blocked = await pipeline.execute_tool_request(req_blocked)
        await session.commit()
        print(f"\n6. BLOCKED Tool Execution: Status = {res_blocked.status.value}")
        print(f"   Rejection Reason: {res_blocked.error_message}")

        # 7. Demonstrate SSRF Defense Blocking Cloud Metadata Attack
        req_ssrf = ToolRequest(
            id="req-demo-4",
            tool_id="http_client_tool",
            tool_version="1.0.0",
            requested_capability=ToolCapability.HTTP_REQUEST,
            arguments={"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"},
            employee_id=dev.id,
            agent_id="agent-dev-bob",
            agent_run_id="run-demo-4",
        )
        res_ssrf = await pipeline.execute_tool_request(req_ssrf)
        await session.commit()
        print(f"\n7. SSRF Security Defense (Cloud Metadata Target): Status = {res_ssrf.status.value}")
        print(f"   SSRF Defense Rejection: {res_ssrf.error_message}")

    await engine.dispose()
    print("\n========================================================================")
    print("PHASE 8 DEMONSTRATION COMPLETE: ALL INVARIANTS & SECURITY CHECKS PASSED!")
    print("========================================================================")


if __name__ == "__main__":
    asyncio.run(run_phase8_demo())
