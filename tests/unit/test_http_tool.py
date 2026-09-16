"""
Unit tests for HTTPToolExecutor and SSRF Defenses.
"""

import pytest

from src.domain.tool import ToolCapability, ToolDefinition, ToolRequest
from src.infrastructure.tools.executors.http_tool_executor import HTTPToolExecutor
from src.infrastructure.tools.sandboxing import SandboxExecutionBoundary, SSRFViolationError


def test_ssrf_validation_loopback_and_metadata() -> None:
    sandbox = SandboxExecutionBoundary()

    # Loopback IP & localhost
    with pytest.raises(SSRFViolationError):
        sandbox.validate_http_url("http://localhost:8000/internal")

    with pytest.raises(SSRFViolationError):
        sandbox.validate_http_url("http://127.0.0.1/admin")

    with pytest.raises(SSRFViolationError):
        sandbox.validate_http_url("http://0.0.0.0/debug")

    # Cloud Metadata IP (169.254.169.254)
    with pytest.raises(SSRFViolationError):
        sandbox.validate_http_url("http://169.254.169.254/latest/meta-data/")

    # Forbidden protocol
    with pytest.raises(SSRFViolationError):
        sandbox.validate_http_url("file:///etc/passwd")

    with pytest.raises(SSRFViolationError):
        sandbox.validate_http_url("gopher://127.0.0.1:70")


@pytest.mark.asyncio
async def test_http_tool_executor_ssrf_blocking() -> None:
    executor = HTTPToolExecutor()
    tool = ToolDefinition(
        id="http_client",
        name="HTTP Client",
        description="Makes HTTP requests",
        capabilities=[ToolCapability.HTTP_REQUEST],
    )
    req = ToolRequest(
        id="req-ssrf",
        tool_id="http_client",
        tool_version="1.0.0",
        requested_capability=ToolCapability.HTTP_REQUEST,
        arguments={"url": "http://169.254.169.254/latest/meta-data/"},
        employee_id="emp-1",
        agent_id="agent-1",
        agent_run_id="run-1",
    )

    result = await executor.execute(req, tool)
    assert result.status.value == "FAILED"
    assert "SSRF Violation" in (result.error_message or "")
