"""
Unit tests for ExecutionStep domain entity.
"""

from src.domain.step import ExecutionStep, StepStatus, StepType


def test_execution_step_creation() -> None:
    step = ExecutionStep(
        id="step_001",
        run_id="run_001",
        step_number=1,
        step_type=StepType.INITIALIZE,
        input_data={"agent_id": "emp_001"},
    )

    assert step.id == "step_001"
    assert step.run_id == "run_001"
    assert step.step_number == 1
    assert step.step_type == StepType.INITIALIZE
    assert step.status == StepStatus.STARTED
    assert step.completed_at is None


def test_execution_step_mark_completed() -> None:
    step = ExecutionStep(
        id="step_002",
        run_id="run_001",
        step_number=2,
        step_type=StepType.BUILD_CONTEXT,
    )

    step.mark_completed(output_data={"context_items_count": 5})

    assert step.status == StepStatus.COMPLETED
    assert step.completed_at is not None
    assert step.output_data == {"context_items_count": 5}


def test_execution_step_mark_failed() -> None:
    step = ExecutionStep(
        id="step_003",
        run_id="run_001",
        step_number=3,
        step_type=StepType.MODEL_CALL,
    )

    step.mark_failed(error_message="Model provider timeout")

    assert step.status == StepStatus.FAILED
    assert step.completed_at is not None
    assert step.error_message == "Model provider timeout"
