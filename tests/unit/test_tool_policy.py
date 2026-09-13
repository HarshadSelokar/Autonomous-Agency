"""
Unit tests for ToolPolicyEngine.
"""

import pytest

from src.application.tool_policy_engine import PolicyDecision, ToolPolicyEngine
from src.domain.employee import Employee, EmployeeStatus
from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolRequest,
    ToolRiskLevel,
)


def test_tool_policy_evaluation_low_risk_auto() -> None:
    engine = ToolPolicyEngine()
    tool = ToolDefinition(
        id="file_read",
        name="File Reader",
        description="Read files",
        capabilities=[ToolCapability.READ_FILE],
        permission_mode=PermissionMode.AUTO,
        risk_level=ToolRiskLevel.LOW,
    )
    req = ToolRequest(
        id="req-1",
        tool_id="file_read",
        tool_version="1.0.0",
        requested_capability=ToolCapability.READ_FILE,
        arguments={},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-1",
    )

    decision = engine.evaluate(tool, req)
    assert decision == PolicyDecision.ALLOW


def test_tool_policy_evaluation_high_risk_requires_approval_for_dev() -> None:
    engine = ToolPolicyEngine()
    tool = ToolDefinition(
        id="delete_file",
        name="File Deleter",
        description="Deletes workspace files",
        capabilities=[ToolCapability.DELETE_FILE],
        permission_mode=PermissionMode.AUTO,
        risk_level=ToolRiskLevel.HIGH,
    )
    req = ToolRequest(
        id="req-2",
        tool_id="delete_file",
        tool_version="1.0.0",
        requested_capability=ToolCapability.DELETE_FILE,
        arguments={"path": "important.txt"},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-2",
    )

    dev_emp = Employee(
        id="emp-dev",
        employee_code="DEV01",
        name="Developer Bob",
        title="Junior Developer",
        role="Software Engineer",
        agent_id="agent-dev",
        status=EmployeeStatus.ACTIVE,
    )

    decision = engine.evaluate(tool, req, actor_employee=dev_emp)
    assert decision == PolicyDecision.REQUIRE_APPROVAL


def test_tool_policy_evaluation_blocked_mode() -> None:
    engine = ToolPolicyEngine()
    tool = ToolDefinition(
        id="blocked_tool",
        name="Forbidden Tool",
        description="Forbidden capability",
        capabilities=[ToolCapability.DATABASE_WRITE],
        permission_mode=PermissionMode.BLOCKED,
    )
    req = ToolRequest(
        id="req-3",
        tool_id="blocked_tool",
        tool_version="1.0.0",
        requested_capability=ToolCapability.DATABASE_WRITE,
        arguments={},
        employee_id="emp-dev",
        agent_id="agent-dev",
        agent_run_id="run-3",
    )

    decision = engine.evaluate(tool, req)
    assert decision == PolicyDecision.DENY
