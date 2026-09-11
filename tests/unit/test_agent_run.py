"""
Unit tests for AgentRun domain entity and state transitions.
"""

import pytest

from src.domain.exceptions import InvalidStateTransitionError
from src.domain.run import AgentRun, RunStatus


def test_agent_run_creation() -> None:
    run = AgentRun(
        id="run_001",
        agent_id="employee_001",
        objective="Analyze DB options for Autonomous AI Platform",
    )

    assert run.id == "run_001"
    assert run.agent_id == "employee_001"
    assert run.status == RunStatus.CREATED
    assert run.started_at is None
    assert run.completed_at is None


def test_valid_agent_run_lifecycle() -> None:
    run = AgentRun(id="run_002", agent_id="emp_100", objective="Test objective")

    # CREATED -> INITIALIZING
    run.transition_to(RunStatus.INITIALIZING)
    assert run.status == RunStatus.INITIALIZING

    # INITIALIZING -> RUNNING
    run.transition_to(RunStatus.RUNNING)
    assert run.status == RunStatus.RUNNING
    assert run.started_at is not None

    # RUNNING -> COMPLETED
    run.transition_to(RunStatus.COMPLETED)
    assert run.status == RunStatus.COMPLETED
    assert run.completed_at is not None


def test_invalid_agent_run_transition_raises_error() -> None:
    run = AgentRun(id="run_003", agent_id="emp_100", objective="Test objective")

    # Attempt CREATED -> COMPLETED directly (invalid)
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        run.transition_to(RunStatus.COMPLETED)

    assert "cannot transition from 'CREATED' to 'COMPLETED'" in str(exc_info.value)
    assert run.status == RunStatus.CREATED


def test_agent_run_failure_transition() -> None:
    run = AgentRun(id="run_004", agent_id="emp_100", objective="Test objective")

    run.transition_to(RunStatus.INITIALIZING)
    run.transition_to(RunStatus.RUNNING)
    run.transition_to(RunStatus.FAILED, failure_reason="Model provider request timed out")

    assert run.status == RunStatus.FAILED
    assert run.completed_at is not None
    assert run.failure_reason == "Model provider request timed out"
