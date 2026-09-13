"""
Unit tests for Tool Domain Entities, Capabilities, and Execution State Machine.
"""

from datetime import UTC, datetime
import pytest

from src.domain.tool import (
    ApprovalStatus,
    PermissionMode,
    ToolApproval,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolExecution,
    ToolExecutionStatus,
    ToolRequest,
    ToolRiskLevel,
    ToolStateError,
    ToolValidationError,
)


def test_tool_definition_validation() -> None:
    tool = ToolDefinition(
        id="file_reader",
        name="File Reader",
        description="Reads workspace files",
        category=ToolCategory.FILESYSTEM,
        capabilities=[ToolCapability.READ_FILE],
        permission_mode=PermissionMode.AUTO,
    )
    assert tool.id == "file_reader"
    assert tool.supports_capability(ToolCapability.READ_FILE)
    assert not tool.supports_capability(ToolCapability.DELETE_FILE)


def test_tool_definition_empty_id_raises() -> None:
    with pytest.raises(ToolValidationError):
        ToolDefinition(
            id="",
            name="Test Tool",
            description="Empty ID test",
            capabilities=[ToolCapability.READ_FILE],
        )


def test_tool_definition_no_capabilities_raises() -> None:
    with pytest.raises(ToolValidationError):
        ToolDefinition(
            id="tool-1",
            name="Test Tool",
            description="No capabilities test",
            capabilities=[],
        )


def test_tool_execution_state_transitions() -> None:
    exec_record = ToolExecution(
        id="exec-1",
        request_id="req-1",
        tool_id="file_reader",
        tool_version="1.0.0",
        capability=ToolCapability.READ_FILE,
        actor_employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
        status=ToolExecutionStatus.REQUESTED,
    )

    exec_record.transition_to(ToolExecutionStatus.VALIDATING)
    assert exec_record.status == ToolExecutionStatus.VALIDATING

    exec_record.transition_to(ToolExecutionStatus.APPROVED)
    assert exec_record.status == ToolExecutionStatus.APPROVED

    exec_record.transition_to(ToolExecutionStatus.EXECUTING)
    assert exec_record.status == ToolExecutionStatus.EXECUTING

    exec_record.transition_to(ToolExecutionStatus.SUCCEEDED)
    assert exec_record.status == ToolExecutionStatus.SUCCEEDED

    # Invalid transition from SUCCEEDED -> EXECUTING
    with pytest.raises(ToolStateError):
        exec_record.transition_to(ToolExecutionStatus.EXECUTING)


def test_tool_approval_flow() -> None:
    approval = ToolApproval(
        id="appr-1",
        execution_id="exec-1",
        tool_id="send_message",
        capability=ToolCapability.SEND_MESSAGE,
        requester_employee_id="emp-dev",
    )
    assert approval.status == ApprovalStatus.PENDING

    approval.approve(approver_employee_id="emp-mgr", rationale="Approved by Lead")
    assert approval.status == ApprovalStatus.APPROVED
    assert approval.approver_employee_id == "emp-mgr"
    assert approval.approved_at is not None
