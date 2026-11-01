"""Unit tests for the Benchmark Harness Service."""

import pytest
from pathlib import Path
from typing import Any
from src.application.agent_engine import AgentTask
from src.application.benchmark_service import BenchmarkHarness
from src.application.dev_team_service import DevTeamOrchestrator, InMemoryDevProjectStore
from src.domain.benchmark import BenchmarkTask
from tests.fixtures.harness import ScriptedTeamHarness


def test_load_benchmark_tasks_from_dir() -> None:
    harness = BenchmarkHarness()
    tasks_dir = Path("benchmarks/tasks")
    tasks = harness.load_tasks_from_dir(tasks_dir)
    assert len(tasks) >= 2
    task_ids = [t.task_id for t in tasks]
    assert "task-health-01" in task_ids
    assert "task-math-02" in task_ids


@pytest.mark.asyncio
async def test_benchmark_harness_executes_task_with_scripted_engine(tmp_path: Path) -> None:
    store = InMemoryDevProjectStore()

    def develop(task: AgentTask, attempt: int) -> None:
        # Developer implements safe_divide in calc.py
        (task.workspace_root / "calc.py").write_text(
            "def safe_divide(a, b):\n    return a / b if b != 0 else None\n",
            encoding="utf-8",
        )

    scripted_engine = ScriptedTeamHarness(
        tickets=[{"title": "implement-calc", "description": "safe divide", "acceptance_criteria": "works"}],
        develop=develop,
    )

    orchestrator = DevTeamOrchestrator(
        store=store,
        engines={"test": scripted_engine, "loop": scripted_engine},
        workspaces_dir=str(tmp_path),
    )

    harness = BenchmarkHarness(workspaces_dir=tmp_path, clean_after=True)
    task = BenchmarkTask(
        task_id="eval-safe-divide",
        title="Safe Divide Test",
        problem_statement="Implement safe_divide",
        test_command="python -c \"import calc; assert calc.safe_divide(6, 2) == 3.0\"",
    )

    result = await harness.run_task(
        task=task,
        engine="test",
        store=store,
        custom_orchestrator=orchestrator,
    )

    assert result.task_id == "eval-safe-divide"
    assert result.success is True
    assert result.status == "COMPLETED"
    assert result.tickets_count == 1
    assert result.tickets_done == 1
    assert result.duration_seconds >= 0.0

