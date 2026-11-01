"""Sandboxed execution harness for running agent tests and commands in isolation."""

import asyncio
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Protocol

from src.infrastructure.coding.command_runner import CommandNotAllowedError, CommandResult, CommandRunner

logger = logging.getLogger(__name__)


class CommandRunnerProtocol(Protocol):
    """Interface for command execution runners."""

    def validate(self, command: str, cwd: Path) -> list[str]: ...

    def run_sync(self, command: str, cwd: Path, timeout_seconds: int | None = None) -> CommandResult: ...

    async def run(self, command: str, cwd: Path, timeout_seconds: int | None = None) -> CommandResult: ...


def is_docker_available() -> bool:
    """Check if docker CLI is installed and the Docker daemon is responding."""
    docker_exe = shutil.which("docker")
    if not docker_exe:
        return False
    try:
        proc = subprocess.run(
            [docker_exe, "info"],
            capture_output=True,
            timeout=3,
            check=False,
        )
        return proc.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


class SandboxedCommandRunner(CommandRunner):
    """
    Sandboxed runner that can execute commands inside an ephemeral Docker container
    with network restriction, memory limits, and filesystem scoping, or fall back
    gracefully to host execution.
    """

    def __init__(
        self,
        mode: str = "local",
        image: str = "python:3.11-slim",
        memory_limit: str = "1g",
        cpus: float = 1.0,
        network_enabled: bool = False,
        local_runner: CommandRunner | None = None,
        allowed_commands: list[str] | None = None,
        timeout_seconds: int = 300,
    ) -> None:
        super().__init__(allowed_commands=allowed_commands, timeout_seconds=timeout_seconds)
        self.mode = mode.lower()
        self.image = image
        self.memory_limit = memory_limit
        self.cpus = cpus
        self.network_enabled = network_enabled
        self.local_runner = local_runner or self
        self._docker_checked = False
        self._docker_ready = False

    @property
    def docker_ready(self) -> bool:
        if not self._docker_checked:
            self._docker_ready = is_docker_available()
            self._docker_checked = True
        return self._docker_ready

    def validate(self, command: str, cwd: Path) -> list[str]:
        if self.local_runner is not self:
            return self.local_runner.validate(command, cwd)
        return super().validate(command, cwd)

    def run_sync(self, command: str, cwd: Path, timeout_seconds: int | None = None) -> CommandResult:
        self.validate(command, cwd)
        timeout = timeout_seconds or 300

        if self.mode == "docker" and self.docker_ready:
            return self._run_in_docker(command, cwd, timeout)

        if self.mode == "docker" and not self.docker_ready:
            logger.warning("Docker requested for sandboxed runner but Docker is not available. Falling back to local execution.")

        if self.local_runner is not self:
            return self.local_runner.run_sync(command, cwd, timeout_seconds)
        return super().run_sync(command, cwd, timeout_seconds)

    def _run_in_docker(self, command: str, cwd: Path, timeout: int) -> CommandResult:
        resolved_cwd = str(cwd.resolve()).replace("\\", "/")
        docker_args = [
            "docker", "run", "--rm",
            "--memory", self.memory_limit,
            f"--cpus={self.cpus}",
            "-v", f"{resolved_cwd}:/workspace",
            "-w", "/workspace",
        ]
        if not self.network_enabled:
            docker_args.extend(["--network", "none"])

        docker_args.extend([self.image, "sh", "-c", command])

        timed_out = False
        try:
            proc = subprocess.run(
                docker_args,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            output = proc.stdout + proc.stderr
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            output = f"[sandboxed container timed out after {timeout}s and was killed]"
            exit_code = -1
        except Exception as exc:
            output = f"[sandboxed container error: {exc}]"
            exit_code = -1

        return CommandResult(
            command=command,
            exit_code=exit_code,
            output=output,
            timed_out=timed_out,
        )

    async def run(self, command: str, cwd: Path, timeout_seconds: int | None = None) -> CommandResult:
        return await asyncio.to_thread(self.run_sync, command, cwd, timeout_seconds)

