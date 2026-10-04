"""
Command runner for agent workspaces.

Runs one allowlisted executable at a time (no shell), inside the workspace directory, with
a timeout, truncated output and secrets stripped from the environment. This is a policy
boundary, not an OS sandbox: an allowed program can still reach the network and the rest of
the filesystem. Run the API inside a container/VM for hard isolation.
"""

import asyncio
import os
import shlex
import shutil
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.infrastructure.config import settings

SHELL_OPERATORS = {"&&", "||", "|", ";", ">", ">>", "<", "&", "2>&1"}
SECRET_ENV_MARKERS = ("KEY", "SECRET", "TOKEN", "PASSWORD", "PASSWD", "CREDENTIAL", "DATABASE_URL", "REDIS_URL")
# git subcommands that reach outside the workspace are reserved for humans
BLOCKED_GIT_SUBCOMMANDS = {"push", "pull", "fetch", "clone", "remote", "submodule"}
PACKAGE_INSTALLERS = {"pip", "pip3", "uv"}


class CommandNotAllowedError(Exception):
    """Raised when a command is rejected by workspace command policy."""


@dataclass
class CommandResult:
    command: str
    exit_code: int
    output: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def _split(command: str) -> list[str]:
    if os.name == "nt":
        # posix=False keeps backslashes in Windows paths; strip the quotes it leaves behind
        tokens = shlex.split(command, posix=False)
        return [t[1:-1] if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'" else t for t in tokens]
    return shlex.split(command)


def _program_name(token: str) -> str:
    name = Path(token).name.lower()
    for suffix in (".exe", ".cmd", ".bat"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


class CommandRunner:
    def __init__(
        self,
        allowed_commands: list[str] | None = None,
        timeout_seconds: int | None = None,
        max_output_chars: int = 12_000,
    ) -> None:
        allowed = allowed_commands if allowed_commands is not None else settings.STUDIO_ALLOWED_COMMANDS
        self.allowed_commands = {c.lower() for c in allowed}
        self.timeout_seconds = timeout_seconds or settings.STUDIO_COMMAND_TIMEOUT_SECONDS
        self.max_output_chars = max_output_chars

    def _venv_bin(self, cwd: Path) -> Path | None:
        candidate = cwd / ".venv" / ("Scripts" if os.name == "nt" else "bin")
        return candidate if candidate.is_dir() else None

    def validate(self, command: str, cwd: Path) -> list[str]:
        """Parse and policy-check a command, returning argv."""
        try:
            argv = _split(command)
        except ValueError as exc:
            raise CommandNotAllowedError(f"Could not parse command: {exc}") from exc
        if not argv:
            raise CommandNotAllowedError("Empty command.")

        if any(token in SHELL_OPERATORS for token in argv):
            raise CommandNotAllowedError(
                "Shell operators (&&, |, >, ;) are not supported. Run one command per call."
            )

        program = _program_name(argv[0])
        if Path(argv[0]).name != argv[0]:
            raise CommandNotAllowedError("Call programs by name, not by path.")
        if program not in self.allowed_commands:
            raise CommandNotAllowedError(
                f"Command '{program}' is not allowed. Allowed: {', '.join(sorted(self.allowed_commands))}."
            )

        lowered = [t.lower() for t in argv[1:]]
        if program == "git" and lowered:
            subcommand = next((t for t in lowered if not t.startswith("-")), "")
            if subcommand in BLOCKED_GIT_SUBCOMMANDS or "--global" in lowered or "--system" in lowered:
                raise CommandNotAllowedError(
                    f"'git {subcommand}' is not available to agents; it needs a human."
                )
        if program in {"npm", "pnpm", "yarn"} and any(t in {"-g", "--global", "global"} for t in lowered):
            raise CommandNotAllowedError("Global package installs are not allowed.")

        installs_python_packages = (program in PACKAGE_INSTALLERS and "install" in lowered) or (
            program in {"python", "python3"} and lowered[:2] == ["-m", "pip"] and "install" in lowered
        )
        if installs_python_packages and self._venv_bin(cwd) is None:
            raise CommandNotAllowedError(
                "Installing Python packages needs a workspace virtualenv. "
                "Create one first with: python -m venv .venv"
            )
        return argv

    def _environment(self, cwd: Path) -> dict[str, str]:
        env = {
            key: value
            for key, value in os.environ.items()
            if not any(marker in key.upper() for marker in SECRET_ENV_MARKERS)
        }
        venv_bin = self._venv_bin(cwd)
        if venv_bin is not None:
            env["PATH"] = f"{venv_bin}{os.pathsep}{env.get('PATH', '')}"
            env["VIRTUAL_ENV"] = str(venv_bin.parent)
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["PYTHONIOENCODING"] = "utf-8"
        # Agents edit and re-run within the same second; a cached .pyc keyed on mtime+size
        # would then run the old code. It also keeps __pycache__ out of commits.
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return env

    def _truncate(self, text: str) -> str:
        if len(text) <= self.max_output_chars:
            return text
        half = self.max_output_chars // 2
        return f"{text[:half]}\n...[{len(text) - 2 * half} characters elided]...\n{text[-half:]}"

    def run_sync(self, command: str, cwd: Path, timeout_seconds: int | None = None) -> CommandResult:
        argv = self.validate(command, cwd)
        env = self._environment(cwd)
        executable = shutil.which(argv[0], path=env.get("PATH"))
        if executable is None:
            return CommandResult(command, 127, f"'{argv[0]}' is not installed on this machine.")

        popen_kwargs: dict = {}
        if os.name == "nt":
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_kwargs["start_new_session"] = True

        process = subprocess.Popen(  # noqa: S603 - argv is policy-checked and never shell-interpreted
            [executable, *argv[1:]],
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **popen_kwargs,
        )
        timeout = timeout_seconds or self.timeout_seconds
        try:
            raw, _ = process.communicate(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            self._kill_tree(process)
            raw, _ = process.communicate()
            timed_out = True

        output = self._truncate(raw.decode("utf-8", errors="replace"))
        if timed_out:
            output += f"\n[command timed out after {timeout}s and was killed]"
        return CommandResult(command, process.returncode if not timed_out else -1, output, timed_out)

    @staticmethod
    def _kill_tree(process: subprocess.Popen) -> None:
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                    check=False,
                )
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, OSError):
            process.kill()

    async def run(self, command: str, cwd: Path, timeout_seconds: int | None = None) -> CommandResult:
        # A worker thread keeps this independent of the event loop's subprocess support on Windows
        return await asyncio.to_thread(self.run_sync, command, cwd, timeout_seconds)
