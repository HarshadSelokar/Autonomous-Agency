"""
Antigravity CLI engine: runs a team member's task with `agy` in headless print mode.

The agent edits files itself; it is not given permission to run commands (headless mode
auto-denies them), so tests are run by the team's QA step under our own command policy.
Progress is read from agy's NDJSON event stream.
"""

import asyncio
import json
import logging
import shutil
import subprocess
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.application.agent_engine import AgentTask
from src.application.agent_loop import AgentLoopResult, EventSink
from src.domain.exceptions import (
    CancellationError,
    ConfigurationError,
    ModelExecutionError,
    QuotaExhaustedError,
)
from src.infrastructure.coding.command_runner import CommandRunner
from src.infrastructure.config import settings

logger = logging.getLogger(__name__)

WRITE_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content", "sed_file", "notebook_edit"}
PATH_PARAMETERS = ("TargetFile", "AbsolutePath", "DirectoryPath", "SearchDirectory", "SearchPath")
BRIEF_DIR_PREFIX = "agy-brief-"

EDITING_RULES = """
Environment rules (these override anything above that conflicts):
- Work only inside the project directory: {root}
- You cannot run commands here. Do not call run_command or any terminal tool: the call is
  denied and your turn ends immediately. The team's QA runs the tests after you finish.
- Make your changes by editing files, then finish with a short summary of what you changed.
"""

READ_ONLY_RULES = """
Environment rules (these override anything above that conflicts):
- The project directory is: {root}
- You may only read. Do not edit files and do not run commands: either call is denied and
  your turn ends immediately.
"""

STRUCTURED_RULE = """
- Ignore any instruction above to call a tool named {tool}. Instead, give your final answer
  as JSON matching the required output schema.
"""


class _Stopped(Exception):
    pass


class AgyEngine:
    def __init__(
        self,
        command: list[str] | None = None,
        timeout_minutes: int | None = None,
        fallback_model: str | None = None,
    ) -> None:
        self.command = command or [settings.AGY_COMMAND]
        self.timeout_minutes = timeout_minutes or settings.AGY_TIMEOUT_MINUTES
        self.fallback_model = (
            fallback_model if fallback_model is not None else settings.AGY_FALLBACK_MODEL
        )

    async def run(
        self,
        task: AgentTask,
        *,
        provider: str,
        model: str,
        on_event: EventSink | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> AgentLoopResult:
        try:
            return await self._run_once(task, model, on_event, should_cancel)
        except ModelExecutionError as exc:
            if not self._is_quota_error(exc):
                raise
            # A model's subscription quota is separate per model; one retry on the fallback
            if not self.fallback_model or self.fallback_model == model:
                raise QuotaExhaustedError(str(exc)) from exc
            logger.warning("agy model %s is out of quota; retrying on %s", model, self.fallback_model)
            if on_event is not None:
                await on_event(
                    {
                        "type": "tool_call",
                        "tool": "switch_model",
                        "arguments": {"from": model, "to": self.fallback_model},
                        "summary": f"out of quota on {model}, switching to {self.fallback_model}",
                    }
                )
            try:
                return await self._run_once(task, self.fallback_model, on_event, should_cancel)
            except ModelExecutionError as fallback_exc:
                if self._is_quota_error(fallback_exc):
                    raise QuotaExhaustedError(str(fallback_exc)) from fallback_exc
                raise

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        text = str(exc).lower()
        return any(marker.lower() in text for marker in settings.AGY_QUOTA_MARKERS)

    def _executable(self) -> list[str]:
        resolved = shutil.which(self.command[0])
        if resolved is None:
            raise ConfigurationError(
                f"The Antigravity CLI '{self.command[0]}' was not found on PATH. "
                "Install it and sign in, or set AGY_COMMAND."
            )
        return [resolved, *self.command[1:]]

    def _brief(self, task: AgentTask) -> str:
        rules = (READ_ONLY_RULES if task.read_only else EDITING_RULES).format(root=task.workspace_root)
        if task.final_tool is not None:
            rules += STRUCTURED_RULE.format(tool=task.final_tool["name"])
        return f"{task.system_prompt}\n\n{task.user_prompt}\n{rules}"

    def _argv(self, task: AgentTask, model: str, brief_path: Path) -> list[str]:
        argv = [
            *self._executable(),
            # The brief can be far longer than a command line allows, so it travels as a file
            f"-p=Read the file {brief_path} and carry out the instructions in it exactly.",
            "--add-dir", str(task.workspace_root),
            "--add-dir", str(brief_path.parent),
            "--output-format", "stream-json",
            "--print-timeout", f"{self.timeout_minutes}m",
        ]
        if model:
            argv += ["--model", model]
        if not task.read_only:
            argv += ["--mode", "accept-edits"]
        if task.final_tool is not None:
            argv += ["--json-schema", json.dumps(task.final_tool["parameters"])]
        return argv

    async def _run_once(
        self,
        task: AgentTask,
        model: str,
        on_event: EventSink | None,
        should_cancel: Callable[[], bool] | None,
    ) -> AgentLoopResult:
        brief_dir = Path(tempfile.mkdtemp(prefix=BRIEF_DIR_PREFIX))
        try:
            brief_path = brief_dir / "brief.md"
            brief_path.write_text(self._brief(task), encoding="utf-8")
            return await self._execute(task, self._argv(task, model, brief_path), on_event, should_cancel)
        finally:
            shutil.rmtree(brief_dir, ignore_errors=True)

    async def _execute(
        self,
        task: AgentTask,
        argv: list[str],
        on_event: EventSink | None,
        should_cancel: Callable[[], bool] | None,
    ) -> AgentLoopResult:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
        stderr_lines: list[str] = []

        process = subprocess.Popen(  # noqa: S603 - fixed executable and argv list, no shell
            argv,
            cwd=str(task.workspace_root),
            env=CommandRunner()._environment(task.workspace_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        def read_stdout() -> None:
            assert process.stdout is not None
            for raw in process.stdout:
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    loop.call_soon_threadsafe(queue.put_nowait, event)
            loop.call_soon_threadsafe(queue.put_nowait, None)

        def read_stderr() -> None:
            assert process.stderr is not None
            for raw in process.stderr:
                stderr_lines.append(raw.decode("utf-8", errors="replace").rstrip())

        # Threads (not asyncio subprocesses) so this works on any Windows event loop
        threading.Thread(target=read_stdout, daemon=True).start()
        threading.Thread(target=read_stderr, daemon=True).start()

        result = AgentLoopResult(final_text="", stop_reason="max_steps")
        final: dict[str, Any] | None = None
        deadline = loop.time() + self.timeout_minutes * 60 + 30
        try:
            while True:
                if should_cancel is not None and should_cancel():
                    raise CancellationError("Agent run cancelled.")
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise _Stopped(f"agy did not finish within {self.timeout_minutes} minutes.")
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=min(remaining, 2.0))
                except TimeoutError:
                    continue
                if event is None:
                    break
                if event.get("event") == "result":
                    final = event.get("result") or {}
                elif event.get("event") == "step_update":
                    await self._on_step(event.get("step_update") or {}, task, result, on_event)
        except (CancellationError, _Stopped) as exc:
            CommandRunner._kill_tree(process)
            if isinstance(exc, CancellationError):
                raise
            raise ModelExecutionError(str(exc)) from exc
        finally:
            await asyncio.to_thread(process.wait)

        stderr_tail = "\n".join(stderr_lines[-5:])
        if final is None:
            raise ModelExecutionError(
                f"agy exited with code {process.returncode} without a result. {stderr_tail}".strip()
            )

        usage = final.get("usage") or {}
        result.usage = {
            "input_tokens": int(usage.get("input_tokens", 0)),
            "output_tokens": int(usage.get("output_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }
        if final.get("status") != "SUCCESS":
            raise ModelExecutionError(
                f"agy run failed ({final.get('status')}): {final.get('error') or stderr_tail}"
            )

        result.final_text = str(final.get("response") or "")
        structured = final.get("structured_output")
        if task.final_tool is not None and isinstance(structured, dict):
            wanted = (task.final_tool["parameters"].get("properties") or {}).keys()
            # agy appends its own bookkeeping keys to the structured answer
            result.final_payload = {k: v for k, v in structured.items() if k in wanted}
        denied = [str(d.get("action")) for d in final.get("denied_actions") or [] if isinstance(d, dict)]
        if denied and not result.final_text:
            # agy reports SUCCESS with an empty answer when a denied action ended the turn
            result.final_text = f"(The agent stopped after a denied action: {', '.join(denied)}.)"
        result.stop_reason = "completed"
        if on_event is not None:
            await on_event({"type": "final", "step": result.steps, "content": result.final_text})
        return result

    async def _on_step(
        self,
        step: dict[str, Any],
        task: AgentTask,
        result: AgentLoopResult,
        on_event: EventSink | None,
    ) -> None:
        if step.get("step_type") != "tool":
            if step.get("step_type") == "agent_response" and step.get("state") == "DONE":
                result.steps += 1
            return
        info = step.get("tool_info") or {}
        name = str(step.get("tool_name") or info.get("name") or "tool")
        parameters = info.get("parameters") if isinstance(info.get("parameters"), dict) else {}
        if BRIEF_DIR_PREFIX in self._path_of(parameters):
            return  # reading its own brief is plumbing, not activity worth showing
        summary = self.describe(name, parameters, task.workspace_root)
        state = step.get("state")
        if on_event is None:
            return

        if state == "ACTIVE":
            result.tool_calls += 1
            await on_event(
                {"type": "tool_call", "step": result.steps, "tool": name, "arguments": parameters, "summary": summary}
            )
            outside = self._outside_workspace(name, parameters, task.workspace_root)
            if outside:
                result.violations.append(f"wrote outside the project: {outside}")
                await on_event(
                    {
                        "type": "tool_result", "step": result.steps, "tool": name, "is_error": True,
                        "summary": "writing outside the project", "preview": outside,
                    }
                )
        elif state == "ERROR":
            error = info.get("error") if isinstance(info.get("error"), dict) else {}
            await on_event(
                {
                    "type": "tool_result", "step": result.steps, "tool": name, "is_error": True,
                    "summary": summary, "preview": str(error.get("message", ""))[:400],
                }
            )

    @staticmethod
    def _path_of(parameters: dict[str, Any]) -> str:
        return next((str(parameters[key]) for key in PATH_PARAMETERS if parameters.get(key)), "")

    @classmethod
    def _relative(cls, parameters: dict[str, Any], root: Path) -> str:
        raw = cls._path_of(parameters)
        if not raw:
            return ""
        try:
            return Path(raw).resolve().relative_to(root.resolve()).as_posix()
        except (ValueError, OSError):
            return Path(raw).name

    @classmethod
    def _outside_workspace(cls, name: str, parameters: dict[str, Any], root: Path) -> str:
        raw = cls._path_of(parameters)
        if name not in WRITE_TOOLS or not raw:
            return ""
        try:
            Path(raw).resolve().relative_to(root.resolve())
            return ""
        except (ValueError, OSError):
            return raw

    @classmethod
    def describe(cls, name: str, parameters: dict[str, Any], root: Path) -> str:
        target = cls._relative(parameters, root)
        if name == "write_to_file":
            return f"writing {target}"
        if name in WRITE_TOOLS:
            return f"editing {target}"
        if name == "view_file":
            return f"reading {target}"
        if name in ("list_dir", "find_by_name"):
            return "looking through the files"
        if name == "grep_search":
            return "searching the code"
        if name == "run_command":
            return f"running {str(parameters.get('CommandLine', ''))[:40]}"
        if name in ("search_web", "read_url_content"):
            return "fetching docs"
        return name.replace("_", " ")
