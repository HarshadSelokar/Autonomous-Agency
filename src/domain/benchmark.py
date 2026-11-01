"""Domain models for the Agent Benchmark & Evaluation Harness."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class BenchmarkTask:
    """A standardized problem specification for evaluating agent engineering capabilities."""

    task_id: str
    title: str
    problem_statement: str
    test_command: str
    repo_path: str = ""
    setup_command: str = ""
    base_commit: str = ""
    golden_patch: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 1200


@dataclass
class BenchmarkTaskResult:
    """Execution and verification outcome for a single benchmark task."""

    task_id: str
    title: str
    success: bool
    status: str
    duration_seconds: float
    tickets_count: int = 0
    tickets_done: int = 0
    tickets_blocked: int = 0
    rework_rounds: int = 0
    diff_chars: int = 0
    test_output_summary: str = ""
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "success": self.success,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "tickets_count": self.tickets_count,
            "tickets_done": self.tickets_done,
            "tickets_blocked": self.tickets_blocked,
            "rework_rounds": self.rework_rounds,
            "diff_chars": self.diff_chars,
            "error_message": self.error_message,
        }


@dataclass
class BenchmarkSuiteResult:
    """Aggregated scorecard across an entire evaluation suite."""

    suite_name: str
    engine: str
    model: str
    results: list[BenchmarkTaskResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def total_tasks(self) -> int:
        return len(self.results)

    @property
    def passed_tasks(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return round((self.passed_tasks / self.total_tasks) * 100.0, 1)

    @property
    def total_duration_seconds(self) -> float:
        return round(sum(r.duration_seconds for r in self.results), 2)

    @property
    def total_rework_rounds(self) -> int:
        return sum(r.rework_rounds for r in self.results)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_name": self.suite_name,
            "engine": self.engine,
            "model": self.model,
            "total_tasks": self.total_tasks,
            "passed_tasks": self.passed_tasks,
            "pass_rate_percent": self.pass_rate,
            "total_duration_seconds": self.total_duration_seconds,
            "total_rework_rounds": self.total_rework_rounds,
            "results": [r.to_dict() for r in self.results],
        }

    def to_markdown_report(self) -> str:
        """Render a clean GitHub Flavored Markdown scorecard table."""
        lines = [
            f"# Benchmark Evaluation Report: {self.suite_name}",
            "",
            f"**Engine**: `{self.engine}` | **Model**: `{self.model or 'default'}`",
            f"**Pass Rate**: **{self.pass_rate}%** ({self.passed_tasks}/{self.total_tasks} passed) | **Total Duration**: {self.total_duration_seconds}s",
            f"**Total Rework Rounds**: {self.total_rework_rounds}",
            "",
            "| Task ID | Title | Status | Result | Duration | Tickets (Done/Total) | Reworks | Diff Size |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in self.results:
            result_icon = "PASS" if r.success else "FAIL"
            lines.append(
                f"| `{r.task_id}` | {r.title} | `{r.status}` | **{result_icon}** | {r.duration_seconds}s | {r.tickets_done}/{r.tickets_count} | {r.rework_rounds} | {r.diff_chars} chars |"
            )
        lines.append("")
        return "\n".join(lines)

