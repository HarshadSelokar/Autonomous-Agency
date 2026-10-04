"""
Coding toolbox: the tools an agent uses to work inside a project workspace.
Implements the AgentToolbox protocol consumed by AgentLoop.
"""

import fnmatch
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from src.application.agent_loop import ToolOutcome
from src.infrastructure.coding.command_runner import CommandNotAllowedError, CommandRunner
from src.infrastructure.coding.workspace import ProjectWorkspace, WorkspaceError

IGNORED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build"}
MAX_FILE_CHARS = 30_000
MAX_LISTED_FILES = 400
MAX_SEARCH_MATCHES = 100

READ_ONLY_TOOLS = ("list_files", "read_file", "search", "git_status", "git_diff")
ALL_TOOLS = (*READ_ONLY_TOOLS, "write_file", "edit_file", "run_command")

_SPECS: dict[str, dict[str, Any]] = {
    "list_files": {
        "name": "list_files",
        "description": "List files in the project (recursively) under a directory.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory, relative to the project root. Default '.'"}},
        },
    },
    "read_file": {
        "name": "read_file",
        "description": "Read a text file. Returns numbered lines.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "description": "First line to read (1-based)."},
                "limit": {"type": "integer", "description": "Maximum number of lines."},
            },
            "required": ["path"],
        },
    },
    "search": {
        "name": "search",
        "description": "Search file contents with a regular expression.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "path": {"type": "string", "description": "Directory to search. Default '.'"},
                "glob": {"type": "string", "description": "Filename filter, e.g. '*.py'."},
            },
            "required": ["pattern"],
        },
    },
    "write_file": {
        "name": "write_file",
        "description": "Create a file or overwrite it with the given content.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
    "edit_file": {
        "name": "edit_file",
        "description": "Replace an exact string in a file. old_string must match exactly and be unique unless replace_all is true.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
                "replace_all": {"type": "boolean"},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    "run_command": {
        "name": "run_command",
        "description": "Run one command in the project root (tests, builds, linters). No shell operators; one program per call.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout_seconds": {"type": "integer"},
            },
            "required": ["command"],
        },
    },
    "git_status": {
        "name": "git_status",
        "description": "Show which files have uncommitted changes.",
        "parameters": {"type": "object", "properties": {}},
    },
    "git_diff": {
        "name": "git_diff",
        "description": "Show the diff of all uncommitted changes.",
        "parameters": {"type": "object", "properties": {}},
    },
}


def _read_exact(path: Path) -> str:
    """Read without newline translation so existing line endings survive an edit."""
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def _write_exact(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


class CodingToolbox:
    def __init__(
        self,
        workspace: ProjectWorkspace,
        runner: CommandRunner | None = None,
        allowed_tools: tuple[str, ...] = ALL_TOOLS,
    ) -> None:
        self.workspace = workspace
        self.runner = runner or CommandRunner()
        self.allowed_tools = allowed_tools
        self._handlers: dict[str, Callable[[dict[str, Any]], Awaitable[ToolOutcome]]] = {
            "list_files": self._list_files,
            "read_file": self._read_file,
            "search": self._search,
            "write_file": self._write_file,
            "edit_file": self._edit_file,
            "run_command": self._run_command,
            "git_status": self._git_status,
            "git_diff": self._git_diff,
        }

    def specs(self) -> list[dict[str, Any]]:
        return [_SPECS[name] for name in self.allowed_tools]

    def describe(self, name: str, arguments: dict[str, Any]) -> str:
        path = str(arguments.get("path") or "")
        if name == "read_file":
            return f"reading {path}"
        if name == "write_file":
            return f"writing {path}"
        if name == "edit_file":
            return f"editing {path}"
        if name == "list_files":
            return "looking through the files"
        if name == "search":
            return f"searching for '{str(arguments.get('pattern', ''))[:40]}'"
        if name == "run_command":
            command = str(arguments.get("command", ""))
            lowered = command.lower()
            if "test" in lowered or "pytest" in lowered:
                return "running tests"
            if "install" in lowered:
                return "installing dependencies"
            if "build" in lowered:
                return "building the project"
            return f"running {command[:40]}"
        if name == "git_status":
            return "checking what changed"
        if name == "git_diff":
            return "reviewing the diff"
        return name

    async def execute(self, name: str, arguments: dict[str, Any]) -> ToolOutcome:
        if name not in self.allowed_tools or name not in self._handlers:
            return ToolOutcome(
                content=f"Unknown or unavailable tool '{name}'. Available: {', '.join(self.allowed_tools)}.",
                is_error=True,
            )
        if "_malformed_arguments" in arguments:
            return ToolOutcome(content="Tool arguments were not valid JSON. Send a JSON object.", is_error=True)
        missing = [key for key in _SPECS[name]["parameters"].get("required", []) if key not in arguments]
        if missing:
            return ToolOutcome(
                content=f"Tool '{name}' is missing required argument(s): {', '.join(missing)}.",
                is_error=True,
            )
        try:
            return await self._handlers[name](arguments)
        except (WorkspaceError, CommandNotAllowedError) as exc:
            return ToolOutcome(content=str(exc), is_error=True)
        except (OSError, UnicodeDecodeError, re.error, TypeError, ValueError) as exc:
            return ToolOutcome(content=f"{type(exc).__name__}: {exc}", is_error=True)

    # --------------------------------------------------------------- handlers
    def _walk(self, start: Path) -> list[Path]:
        files: list[Path] = []
        stack = [start]
        while stack:
            current = stack.pop()
            for entry in sorted(current.iterdir(), key=lambda p: p.name):
                if entry.is_dir():
                    if entry.name not in IGNORED_DIRS:
                        stack.append(entry)
                elif entry.is_file():
                    files.append(entry)
        # Sort on the posix path string so the order is the same on every platform
        return sorted(files, key=lambda p: p.as_posix())

    async def _list_files(self, args: dict[str, Any]) -> ToolOutcome:
        start = self.workspace.resolve(str(args.get("path") or "."))
        if not start.is_dir():
            return ToolOutcome(content=f"'{args.get('path')}' is not a directory.", is_error=True)
        files = self._walk(start)
        lines = [self.workspace.relative(f) for f in files[:MAX_LISTED_FILES]]
        if len(files) > MAX_LISTED_FILES:
            lines.append(f"...and {len(files) - MAX_LISTED_FILES} more files")
        return ToolOutcome(content="\n".join(lines) or "(no files)")

    async def _read_file(self, args: dict[str, Any]) -> ToolOutcome:
        target = self.workspace.resolve(str(args["path"]))
        if not target.is_file():
            return ToolOutcome(content=f"File '{args['path']}' does not exist.", is_error=True)
        lines = target.read_text(encoding="utf-8").splitlines()
        offset = max(int(args.get("offset") or 1), 1)
        limit = int(args.get("limit") or len(lines) or 1)
        selected = lines[offset - 1 : offset - 1 + limit]
        body = "\n".join(f"{offset + i}\t{line}" for i, line in enumerate(selected))
        if len(body) > MAX_FILE_CHARS:
            body = body[:MAX_FILE_CHARS] + "\n...[truncated; use offset/limit to read further]"
        return ToolOutcome(content=body or "(empty file)")

    async def _search(self, args: dict[str, Any]) -> ToolOutcome:
        regex = re.compile(str(args["pattern"]))
        start = self.workspace.resolve(str(args.get("path") or "."))
        glob = args.get("glob")
        files = self._walk(start) if start.is_dir() else [start]
        matches: list[str] = []
        for file in files:
            if glob and not fnmatch.fnmatch(file.name, str(glob)):
                continue
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    matches.append(f"{self.workspace.relative(file)}:{number}: {line.strip()[:200]}")
                    if len(matches) >= MAX_SEARCH_MATCHES:
                        matches.append("...more matches not shown")
                        return ToolOutcome(content="\n".join(matches))
        return ToolOutcome(content="\n".join(matches) or "No matches.")

    async def _write_file(self, args: dict[str, Any]) -> ToolOutcome:
        target = self.workspace.resolve(str(args["path"]))
        content = str(args.get("content", ""))
        target.parent.mkdir(parents=True, exist_ok=True)
        _write_exact(target, content)
        return ToolOutcome(content=f"Wrote {len(content)} characters to {args['path']}.")

    async def _edit_file(self, args: dict[str, Any]) -> ToolOutcome:
        target = self.workspace.resolve(str(args["path"]))
        if not target.is_file():
            return ToolOutcome(content=f"File '{args['path']}' does not exist.", is_error=True)
        old, new = str(args["old_string"]), str(args["new_string"])
        text = _read_exact(target)
        if "\r\n" in text:
            # Models send LF; match the file's CRLF line endings instead of rewriting them
            old = old.replace("\r\n", "\n").replace("\n", "\r\n")
            new = new.replace("\r\n", "\n").replace("\n", "\r\n")
        occurrences = text.count(old)
        if occurrences == 0:
            return ToolOutcome(content="old_string was not found in the file. Read the file and retry.", is_error=True)
        if occurrences > 1 and not args.get("replace_all"):
            return ToolOutcome(
                content=f"old_string matches {occurrences} times. Add surrounding context or set replace_all.",
                is_error=True,
            )
        updated = text.replace(old, new) if args.get("replace_all") else text.replace(old, new, 1)
        _write_exact(target, updated)
        return ToolOutcome(content=f"Edited {args['path']} ({occurrences if args.get('replace_all') else 1} replacement).")

    async def _run_command(self, args: dict[str, Any]) -> ToolOutcome:
        command = str(args["command"])
        timeout = args.get("timeout_seconds")
        result = await self.runner.run(command, self.workspace.root, int(timeout) if timeout else None)
        return ToolOutcome(
            content=f"exit code: {result.exit_code}\n{result.output}".strip(),
            is_error=not result.ok,
        )

    async def _git_status(self, args: dict[str, Any]) -> ToolOutcome:
        return ToolOutcome(content=(await self.workspace.status()) or "Working tree clean.")

    async def _git_diff(self, args: dict[str, Any]) -> ToolOutcome:
        return ToolOutcome(content=(await self.workspace.pending_diff()) or "No uncommitted changes.")
