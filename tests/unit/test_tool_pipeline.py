"""
Unit tests for ToolApprovalService and ToolExecutionPipeline.
"""

import pytest

from src.application.tool_approval_service import ToolApprovalService, UnauthorizedApprovalError
from src.application.tool_execution_pipeline import ToolExecutionPipeline
from src.application.tool_registry import ToolRegistry
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


@pytest.mark.asyncio
async def test_approval_parameter_tampering_rejected(pipeline_setup) -> None:
    """Verifies SEC-02: Tampering with parameters after approval is cryptographically rejected."""
    _, pipeline, approval_service = pipeline_setup

    req = ToolRequest(
        id="req-tamper-1",
        tool_id="send_msg",
        tool_version="1.0.0",
        requested_capability=ToolCapability.SEND_MESSAGE,
        arguments={"recipient_id": "emp-mgr", "content": "Safe content approved"},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-tamper",
    )
    res = await pipeline.execute_tool_request(req)
    approval_id = res.output["approval_id"]
    await approval_service.approve_request(approval_id, approver_employee_id="emp-mgr")

    # Attacker attempts parameter substitution attack
    tampered_req = ToolRequest(
        id="req-tamper-2",
        tool_id="send_msg",
        tool_version="1.0.0",
        requested_capability=ToolCapability.SEND_MESSAGE,
        arguments={"recipient_id": "emp-mgr", "content": "MALICIOUS TAMPERED PAYLOAD"},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-tamper",
    )
    tampered_result = await pipeline.execute_tool_request(tampered_req, pre_approved_approval_id=approval_id)
    assert tampered_result.status == ToolExecutionStatus.DENIED
    assert "parameter hash mismatch" in (tampered_result.error_message or "").lower()


@pytest.mark.asyncio
async def test_approval_replay_rejected(pipeline_setup) -> None:
    """Verifies SEC-02: An approval grant cannot be replayed or reused once consumed."""
    _, pipeline, approval_service = pipeline_setup

    req = ToolRequest(
        id="req-replay-1",
        tool_id="send_msg",
        tool_version="1.0.0",
        requested_capability=ToolCapability.SEND_MESSAGE,
        arguments={"recipient_id": "emp-mgr", "content": "Single-use operation"},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-replay",
    )
    res = await pipeline.execute_tool_request(req)
    approval_id = res.output["approval_id"]
    await approval_service.approve_request(approval_id, approver_employee_id="emp-mgr")

    # First execution succeeds and consumes the approval
    first_exec = await pipeline.execute_tool_request(req, pre_approved_approval_id=approval_id)
    assert first_exec.status == ToolExecutionStatus.SUCCEEDED

    # Replay attack with same approval ID
    replay_exec = await pipeline.execute_tool_request(req, pre_approved_approval_id=approval_id)
    assert replay_exec.status == ToolExecutionStatus.DENIED
    assert "already been consumed" in (replay_exec.error_message or "").lower()


@pytest.mark.asyncio
async def test_approval_expiration_rejected(pipeline_setup) -> None:
    """Verifies SEC-02: An expired approval grant cannot be executed."""
    from datetime import UTC, datetime, timedelta
    _, pipeline, approval_service = pipeline_setup

    req = ToolRequest(
        id="req-expire-1",
        tool_id="send_msg",
        tool_version="1.0.0",
        requested_capability=ToolCapability.SEND_MESSAGE,
        arguments={"recipient_id": "emp-mgr", "content": "Expiring action"},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-expire",
    )
    res = await pipeline.execute_tool_request(req)
    approval_id = res.output["approval_id"]
    appr = await approval_service.approve_request(approval_id, approver_employee_id="emp-mgr")

    # Manually expire the approval token
    appr.expires_at = datetime.now(UTC) - timedelta(seconds=10)

    expired_exec = await pipeline.execute_tool_request(req, pre_approved_approval_id=approval_id)
    assert expired_exec.status == ToolExecutionStatus.DENIED
    assert "expired" in (expired_exec.error_message or "").lower()

