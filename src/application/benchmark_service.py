"""Benchmark & Evaluation Harness Service for evaluating autonomous agent performance."""

import asyncio
import json
import logging
import os
import shutil
import stat
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.application.dev_team_service import (
    DevProjectStore,
    DevTeamOrchestrator,
    InMemoryDevProjectStore,
)
from src.domain.benchmark import BenchmarkSuiteResult, BenchmarkTask, BenchmarkTaskResult
from src.domain.dev_project import DevProject, ProjectStatus, default_team
from src.infrastructure.coding.command_runner import CommandRunner
from src.infrastructure.coding.sandboxed_runner import SandboxedCommandRunner
from src.infrastructure.coding.workspace import ProjectWorkspace

logger = logging.getLogger(__name__)


def _rmtree_force(path: Path) -> None:
    def on_err(func: Any, failed_path: str, _: Any) -> None:
        os.chmod(failed_path, stat.S_IWRITE)
        func(failed_path)

    if path.exists():
        shutil.rmtree(path, onerror=on_err)


class BenchmarkHarness:
    """Orchestrates benchmark task execution, metric collection, and scorecard generation."""

    def __init__(
        self,
        workspaces_dir: Path | None = None,
        runner_mode: str = "local",
        clean_after: bool = True,
    ) -> None:
        self.workspaces_dir = workspaces_dir or Path("scratch/benchmarks")
        self.runner_mode = runner_mode
        self.clean_after = clean_after
        self.runner = SandboxedCommandRunner(mode=runner_mode)

    @staticmethod
    def load_task_from_dict(data: dict[str, Any]) -> BenchmarkTask:
        return BenchmarkTask(
            task_id=str(data["task_id"]),
            title=str(data.get("title", data["task_id"])),
            problem_statement=str(data["problem_statement"]),
            test_command=str(data["test_command"]),
            repo_path=str(data.get("repo_path", "")),
            setup_command=str(data.get("setup_command", "")),
            base_commit=str(data.get("base_commit", "")),
            golden_patch=str(data.get("golden_patch", "")),
            metadata=dict(data.get("metadata", {})),
            timeout_seconds=int(data.get("timeout_seconds", 1200)),
        )

    @classmethod
    def load_task_from_file(cls, path: Path) -> BenchmarkTask:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.load_task_from_dict(data)

    @classmethod
    def load_tasks_from_dir(cls, directory: Path) -> list[BenchmarkTask]:
        tasks: list[BenchmarkTask] = []
        for file in sorted(directory.glob("*.json")):
            try:
                tasks.append(cls.load_task_from_file(file))
            except Exception as exc:
                logger.warning("Failed to load benchmark task from %s: %exc", file, exc)
        return tasks

    async def run_task(
        self,
        task: BenchmarkTask,
        engine: str = "loop",
        model: str = "",
        developers: int = 2,
        store: DevProjectStore | None = None,
        custom_orchestrator: DevTeamOrchestrator | None = None,
    ) -> BenchmarkTaskResult:
        """Run an autonomous agent team against a single benchmark task and record metrics."""
        task_ws_dir = self.workspaces_dir / f"bench-{task.task_id}"
        task_ws_dir.parent.mkdir(parents=True, exist_ok=True)

        store = store or InMemoryDevProjectStore()
        orchestrator = custom_orchestrator or DevTeamOrchestrator(
            store=store,
            runner=self.runner,
            workspaces_dir=str(task_ws_dir.parent),
        )

        project = DevProject(
            id=f"bench-{task.task_id}",
            name=task.title,
            goal=task.problem_statement,
            local_path=task.repo_path,
            test_command=task.test_command,
            engine=engine,
            model=model,
        )
        project.set_team(default_team(project.id, developers))
        await store.save_project(project)

        start_time = time.time()
        error_msg: str | None = None
        result_status = "UNKNOWN"
        tickets_count = 0
        tickets_done = 0
        tickets_blocked = 0
        rework_rounds = 0
        diff_chars = 0

        try:
            res = await orchestrator.run_project(project.id)
            result_status = res.status.value
            duration = round(time.time() - start_time, 2)

            tickets = await store.list_tickets(project.id)
            tickets_count = len(tickets)
            tickets_done = sum(1 for t in tickets if t.status.value == "DONE")
            tickets_blocked = sum(1 for t in tickets if t.status.value == "BLOCKED")
            rework_rounds = sum(t.attempts for t in tickets)

            if res.workspace_path and Path(res.workspace_path).is_dir():
                try:
                    workspace = ProjectWorkspace(Path(res.workspace_path))
                    diff = await workspace.diff(res.base_commit)
                    diff_chars = len(diff)
                except Exception:
                    diff_chars = 0

            success = (res.status == ProjectStatus.COMPLETED)
            if not success and res.failure_reason:
                error_msg = res.failure_reason

        except Exception as exc:
            duration = round(time.time() - start_time, 2)
            result_status = "FAILED"
            success = False
            error_msg = str(exc)
            logger.exception("Benchmark task %s encountered an error", task.task_id)

        finally:
            if self.clean_after:
                _rmtree_force(task_ws_dir)
                _rmtree_force(task_ws_dir.parent / f"{task_ws_dir.name}.worktrees")

        return BenchmarkTaskResult(
            task_id=task.task_id,
            title=task.title,
            success=success,
            status=result_status,
            duration_seconds=duration,
            tickets_count=tickets_count,
            tickets_done=tickets_done,
            tickets_blocked=tickets_blocked,
            rework_rounds=rework_rounds,
            diff_chars=diff_chars,
            error_message=error_msg,
        )

    async def run_suite(
        self,
        suite_name: str,
        tasks: list[BenchmarkTask],
        engine: str = "loop",
        model: str = "",
        developers: int = 2,
    ) -> BenchmarkSuiteResult:
        """Run all tasks in a benchmark suite and return the aggregated scorecard."""
        start_time = datetime.now(UTC)
        results: list[BenchmarkTaskResult] = []

        for task in tasks:
            logger.info("Starting benchmark task: %s - %s", task.task_id, task.title)
            task_result = await self.run_task(task, engine=engine, model=model, developers=developers)
            results.append(task_result)

        end_time = datetime.now(UTC)
        return BenchmarkSuiteResult(
            suite_name=suite_name,
            engine=engine,
            model=model,
            results=results,
            start_time=start_time,
            end_time=end_time,
        )
