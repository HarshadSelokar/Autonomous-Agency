"""Unit tests for Benchmark domain entities and scorecards."""

from src.domain.benchmark import BenchmarkSuiteResult, BenchmarkTask, BenchmarkTaskResult


def test_benchmark_task_instantiation():
    task = BenchmarkTask(
        task_id="task-01",
        title="Add health check",
        problem_statement="Write health.py",
        test_command="python -m pytest",
        timeout_seconds=300,
    )
    assert task.task_id == "task-01"
    assert task.title == "Add health check"
    assert task.timeout_seconds == 300


def test_benchmark_suite_result_scorecard():
    r1 = BenchmarkTaskResult(
        task_id="t1",
        title="First Task",
        success=True,
        status="COMPLETED",
        duration_seconds=12.5,
        tickets_count=2,
        tickets_done=2,
        tickets_blocked=0,
        rework_rounds=1,
        diff_chars=120,
    )
    r2 = BenchmarkTaskResult(
        task_id="t2",
        title="Second Task",
        success=False,
        status="NEEDS_ATTENTION",
        duration_seconds=30.0,
        tickets_count=1,
        tickets_done=0,
        tickets_blocked=1,
        rework_rounds=3,
        diff_chars=50,
        error_message="Test failed",
    )

    suite = BenchmarkSuiteResult(
        suite_name="Unit Eval",
        engine="loop",
        model="gpt-4o",
        results=[r1, r2],
    )

    assert suite.total_tasks == 2
    assert suite.passed_tasks == 1
    assert suite.pass_rate == 50.0
    assert suite.total_duration_seconds == 42.5
    assert suite.total_rework_rounds == 4

    report = suite.to_markdown_report()
    assert "# Benchmark Evaluation Report: Unit Eval" in report
    assert "**Pass Rate**: **50.0%**" in report
    assert "`t1`" in report
    assert "`t2`" in report
    assert "**PASS**" in report
    assert "**FAIL**" in report

    data = suite.to_dict()
    assert data["suite_name"] == "Unit Eval"
    assert data["pass_rate_percent"] == 50.0
    assert len(data["results"]) == 2
