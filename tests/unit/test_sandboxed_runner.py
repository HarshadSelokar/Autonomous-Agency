"""Unit tests for the Sandboxed Command Runner harness."""

from pathlib import Path
import pytest
from src.infrastructure.coding.command_runner import CommandNotAllowedError
from src.infrastructure.coding.sandboxed_runner import SandboxedCommandRunner, is_docker_available


def test_sandboxed_runner_local_mode(tmp_path: Path) -> None:
    runner = SandboxedCommandRunner(mode="local")
    result = runner.run_sync("python -c \"print('harness ok')\"", tmp_path)
    assert result.ok is True
    assert "harness ok" in result.output


def test_sandboxed_runner_validates_blocked_subcommands(tmp_path: Path) -> None:
    runner = SandboxedCommandRunner(mode="local")
    with pytest.raises(CommandNotAllowedError, match="not available to agents"):
        runner.validate("git push origin main", tmp_path)


def test_sandboxed_runner_docker_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate Docker not being available
    monkeypatch.setattr("src.infrastructure.coding.sandboxed_runner.is_docker_available", lambda: False)
    runner = SandboxedCommandRunner(mode="docker")
    assert runner.docker_ready is False

    # Falls back to local execution cleanly
    result = runner.run_sync("python -c \"print('fallback executed')\"", tmp_path)
    assert result.ok is True
    assert "fallback executed" in result.output
