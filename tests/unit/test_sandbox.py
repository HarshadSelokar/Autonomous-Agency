"""
Unit tests for SandboxExecutionBoundary and path sanitization.
"""

import pytest

from src.infrastructure.tools.sandboxing import (
    SandboxExecutionBoundary,
    SandboxViolationError,
)


def test_sandbox_path_sanitization_valid() -> None:
    sandbox = SandboxExecutionBoundary(base_workspace_dir="scratch/test_sandbox")
    sanitized = sandbox.sanitize_path("reports/summary.md", workspace_id="ws-100")
    assert "ws-100" in str(sanitized)
    assert sanitized.name == "summary.md"


def test_sandbox_directory_traversal_prevention() -> None:
    sandbox = SandboxExecutionBoundary(base_workspace_dir="scratch/test_sandbox")
    with pytest.raises(SandboxViolationError):
        sandbox.sanitize_path("../../../etc/passwd", workspace_id="ws-100")


def test_sandbox_output_truncation() -> None:
    sandbox = SandboxExecutionBoundary(max_output_size_bytes=50)
    large_text = "A" * 100
    truncated = sandbox.truncate_output(large_text)
    assert len(truncated.encode("utf-8")) < 100
    assert "[OUTPUT TRUNCATED BY SANDBOX]" in truncated
