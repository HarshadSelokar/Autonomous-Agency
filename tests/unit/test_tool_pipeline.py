"""
Unit tests for ToolApprovalService and ToolExecutionPipeline.
"""

import pytest

from src.application.tool_approval_service import ToolApprovalService, UnauthorizedApprovalError
from src.application.tool_execution_pipeline import ToolExecutionPipeline
from src.application.tool_registry import ToolRegistry
from src.domain.employee import Employee, EmployeeStatus
from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolExecutionStatus,
    ToolRequest,
)


@pytest.fixture
def pipeline_setup() -> tuple[ToolRegistry, ToolExecutionPipeline, ToolApprovalService]:
    reg = ToolRegistry()
    file_tool = ToolDefinition(
        id="file_writer",
        name="File Writer",
        description="Writes files",
        category=ToolCategory.FILESYSTEM,
        capabilities=[ToolCapability.WRITE_FILE],
        permission_mode=PermissionMode.AUTO,
    )
    msg_tool = ToolDefinition(
        id="send_msg",
        name="Message Sender",
        description="Sends external messages",
        category=ToolCategory.COMMUNICATION,
        capabilities=[ToolCapability.SEND_MESSAGE],
        permission_mode=PermissionMode.APPROVAL,
    )
    reg.register(file_tool)
    reg.register(msg_tool)

    approval_service = ToolApprovalService()
    pipeline = ToolExecutionPipeline(registry=reg, approval_service=approval_service)
    return reg, pipeline, approval_service


@pytest.mark.asyncio
async def test_pipeline_auto_execution(pipeline_setup) -> None:
    _, pipeline, _ = pipeline_setup
    req = ToolRequest(
        id="req-1",
        tool_id="file_writer",
        tool_version="1.0.0",
        requested_capability=ToolCapability.WRITE_FILE,
        arguments={"path": "notes.txt", "content": "Hello World"},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-1",
        workspace_id="ws-100",
    )

    result = await pipeline.execute_tool_request(req)
    assert result.status == ToolExecutionStatus.SUCCEEDED
    assert result.output["path"] == "notes.txt"
    assert result.output["written_bytes"] == 11
    assert result.evidence_id is not None


@pytest.mark.asyncio
async def test_pipeline_approval_workflow_requires_approval(pipeline_setup) -> None:
    _, pipeline, approval_service = pipeline_setup

    req = ToolRequest(
        id="req-2",
        tool_id="send_msg",
        tool_version="1.0.0",
        requested_capability=ToolCapability.SEND_MESSAGE,
        arguments={"recipient_id": "emp-mgr", "content": "Need budget approval"},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-2",
    )

    # Step 1: Execute -> Should enter PENDING_APPROVAL
    result = await pipeline.execute_tool_request(req)
    assert result.status == ToolExecutionStatus.PENDING_APPROVAL
    approval_id = result.output["approval_id"]

    # Step 2: Requester trying to approve their OWN request -> UnauthorizedApprovalError
    with pytest.raises(UnauthorizedApprovalError):
        await approval_service.approve_request(approval_id, approver_employee_id="emp-dev")

    # Step 3: Manager approves request
    appr = await approval_service.approve_request(approval_id, approver_employee_id="emp-mgr")
    assert appr.status.value == "APPROVED"

    # Step 4: Re-execute pipeline with pre-approved ID -> SUCCEEDED
    exec_result = await pipeline.execute_tool_request(req, pre_approved_approval_id=approval_id)
    assert exec_result.status == ToolExecutionStatus.SUCCEEDED
    assert exec_result.output["delivered"] is True
