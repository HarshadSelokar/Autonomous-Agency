"""
Failure injection test suite for Phase 8 Tools & Integrations.
"""

import pytest

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


@pytest.mark.asyncio
async def test_failure_injection_unknown_tool() -> None:
    registry = ToolRegistry()
    pipeline = ToolExecutionPipeline(registry=registry)

    req = ToolRequest(
        id="req-fail-1",
        tool_id="unknown_tool_xyz",
        tool_version="1.0.0",
        requested_capability=ToolCapability.READ_FILE,
        arguments={},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )

    res = await pipeline.execute_tool_request(req)
    assert res.status == ToolExecutionStatus.DENIED
    assert "unknown or inactive" in (res.error_message or "")


@pytest.mark.asyncio
async def test_failure_injection_capability_mismatch() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            id="reader_only",
            name="Reader Only",
            description="Reads files",
            capabilities=[ToolCapability.READ_FILE],
        )
    )
    pipeline = ToolExecutionPipeline(registry=registry)

    req = ToolRequest(
        id="req-fail-2",
        tool_id="reader_only",
        tool_version="1.0.0",
        requested_capability=ToolCapability.DELETE_FILE,  # Mismatch!
        arguments={"path": "doc.txt"},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )

    res = await pipeline.execute_tool_request(req)
    assert res.status == ToolExecutionStatus.DENIED
    assert "does NOT support requested capability" in (res.error_message or "")


@pytest.mark.asyncio
async def test_failure_injection_blocked_mode() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            id="db_drop",
            name="Drop DB",
            description="Drops DB",
            capabilities=[ToolCapability.DATABASE_WRITE],
            permission_mode=PermissionMode.BLOCKED,
        )
    )
    pipeline = ToolExecutionPipeline(registry=registry)

    req = ToolRequest(
        id="req-fail-3",
        tool_id="db_drop",
        tool_version="1.0.0",
        requested_capability=ToolCapability.DATABASE_WRITE,
        arguments={},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )

    res = await pipeline.execute_tool_request(req)
    assert res.status == ToolExecutionStatus.DENIED
    assert "BLOCKED by organizational policy" in (res.error_message or "")


@pytest.mark.asyncio
async def test_failure_injection_ssrf_metadata_attack() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            id="http_fetch",
            name="HTTP Fetch",
            description="Fetches URL",
            category=ToolCategory.HTTP,
            capabilities=[ToolCapability.HTTP_REQUEST],
        )
    )
    pipeline = ToolExecutionPipeline(registry=registry)

    req = ToolRequest(
        id="req-fail-4",
        tool_id="http_fetch",
        tool_version="1.0.0",
        requested_capability=ToolCapability.HTTP_REQUEST,
        arguments={"url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )

    res = await pipeline.execute_tool_request(req)
    assert res.status == ToolExecutionStatus.FAILED
    assert "SSRF Violation" in (res.error_message or "")
