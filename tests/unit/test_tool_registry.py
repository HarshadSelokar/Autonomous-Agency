"""
Unit tests for ToolRegistry and ToolResolver.
"""

import pytest

from src.application.tool_registry import ToolRegistry
from src.application.tool_resolver import ToolResolver
from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolRequest,
    ToolRiskLevel,
)


@pytest.fixture
def sample_registry() -> ToolRegistry:
    reg = ToolRegistry()
    file_tool = ToolDefinition(
        id="file_tool",
        name="Workspace File Tool",
        description="Reads workspace files",
        category=ToolCategory.FILESYSTEM,
        capabilities=[ToolCapability.READ_FILE, ToolCapability.WRITE_FILE],
        permission_mode=PermissionMode.AUTO,
    )
    comm_tool = ToolDefinition(
        id="send_message",
        name="Communication Tool",
        description="Sends external messages",
        category=ToolCategory.COMMUNICATION,
        capabilities=[ToolCapability.SEND_MESSAGE],
        permission_mode=PermissionMode.APPROVAL,
    )
    blocked_tool = ToolDefinition(
        id="delete_db",
        name="DB Delete Tool",
        description="Deletes databases",
        category=ToolCategory.DATABASE,
        capabilities=[ToolCapability.DATABASE_WRITE],
        permission_mode=PermissionMode.BLOCKED,
        risk_level=ToolRiskLevel.CRITICAL,
    )
    reg.register(file_tool)
    reg.register(comm_tool)
    reg.register(blocked_tool)
    return reg


def test_registry_lookup_and_filtering(sample_registry: ToolRegistry) -> None:
    tool = sample_registry.get_tool("file_tool")
    assert tool is not None
    assert tool.name == "Workspace File Tool"

    # Capability filter
    comm_tools = sample_registry.list_tools(capability=ToolCapability.SEND_MESSAGE)
    assert len(comm_tools) == 1
    assert comm_tools[0].id == "send_message"

    # Agent metadata exposure (no secret keys)
    safe_meta = sample_registry.get_safe_metadata_for_agent()
    assert len(safe_meta) == 3
    assert all("tool_id" in m and "capabilities" in m for m in safe_meta)


def test_resolver_auto_mode(sample_registry: ToolRegistry) -> None:
    resolver = ToolResolver(sample_registry)
    req = ToolRequest(
        id="req-1",
        tool_id="file_tool",
        tool_version="1.0.0",
        requested_capability=ToolCapability.READ_FILE,
        arguments={"path": "doc.txt"},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )

    result = resolver.resolve(req)
    assert result.is_allowed is True
    assert result.requires_approval is False
    assert result.tool is not None


def test_resolver_approval_mode(sample_registry: ToolRegistry) -> None:
    resolver = ToolResolver(sample_registry)
    req = ToolRequest(
        id="req-2",
        tool_id="send_message",
        tool_version="1.0.0",
        requested_capability=ToolCapability.SEND_MESSAGE,
        arguments={"recipient": "boss@company.com"},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )

    result = resolver.resolve(req)
    assert result.is_allowed is False
    assert result.requires_approval is True
    assert "requires explicit managerial approval" in (result.rejection_reason or "")


def test_resolver_blocked_mode(sample_registry: ToolRegistry) -> None:
    resolver = ToolResolver(sample_registry)
    req = ToolRequest(
        id="req-3",
        tool_id="delete_db",
        tool_version="1.0.0",
        requested_capability=ToolCapability.DATABASE_WRITE,
        arguments={"db": "prod"},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )

    result = resolver.resolve(req)
    assert result.is_allowed is False
    assert result.requires_approval is False
    assert "is BLOCKED" in (result.rejection_reason or "")


def test_resolver_unknown_tool_or_invalid_capability(sample_registry: ToolRegistry) -> None:
    resolver = ToolResolver(sample_registry)

    # Unknown tool
    req_unknown = ToolRequest(
        id="req-4",
        tool_id="non_existent",
        tool_version="1.0.0",
        requested_capability=ToolCapability.READ_FILE,
        arguments={},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )
    res_unknown = resolver.resolve(req_unknown)
    assert res_unknown.is_allowed is False
    assert "unknown or inactive" in (res_unknown.rejection_reason or "")

    # Invalid capability requested
    req_bad_cap = ToolRequest(
        id="req-5",
        tool_id="file_tool",
        tool_version="1.0.0",
        requested_capability=ToolCapability.SEND_MESSAGE,  # file_tool doesn't support SEND_MESSAGE
        arguments={},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )
    res_bad_cap = resolver.resolve(req_bad_cap)
    assert res_bad_cap.is_allowed is False
    assert "does NOT support requested capability" in (res_bad_cap.rejection_reason or "")
