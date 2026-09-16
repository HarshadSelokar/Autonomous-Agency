"""
Unit tests for Swarm domain model, state transitions, members, and budget rules (Phase 22).
"""

import pytest
from datetime import UTC, datetime

from src.domain.exceptions import InvalidStateTransitionError, SwarmValidationError
from src.domain.swarm import (
    CoordinationMode,
    Swarm,
    SwarmBudget,
    SwarmMember,
    SwarmMemberStatus,
    SwarmStatus,
)


def test_swarm_creation_and_defaults():
    swarm = Swarm(
        id="swarm-001",
        name="Software Debug Swarm",
        code="SW-DBG-1",
        parent_task_id="task-100",
        purpose="Debug memory leak in worker queue",
        manager_id="emp-mgr-1",
    )
    assert swarm.status == SwarmStatus.CREATED
    assert swarm.coordination_mode == CoordinationMode.PARALLEL
    assert swarm.depth == 1
    assert len(swarm.members) == 0


def test_swarm_valid_state_transitions():
    swarm = Swarm(
        id="swarm-001",
        name="Security Review Swarm",
        code="SW-SEC-1",
        parent_task_id="task-101",
        purpose="Conduct automated audit",
        manager_id="emp-mgr-1",
    )

    swarm.transition_to(SwarmStatus.PLANNING)
    assert swarm.status == SwarmStatus.PLANNING

    swarm.transition_to(SwarmStatus.FORMING)
    assert swarm.status == SwarmStatus.FORMING

    swarm.transition_to(SwarmStatus.READY)
    assert swarm.status == SwarmStatus.READY

    swarm.transition_to(SwarmStatus.RUNNING)
    assert swarm.status == SwarmStatus.RUNNING
    assert swarm.started_at is not None

    swarm.transition_to(SwarmStatus.COMPLETING)
    swarm.transition_to(SwarmStatus.VERIFYING)
    swarm.transition_to(SwarmStatus.COMPLETED)
    assert swarm.status == SwarmStatus.COMPLETED
    assert swarm.completed_at is not None


def test_swarm_invalid_state_transition_raises():
    swarm = Swarm(
        id="swarm-002",
        name="Invalid Transition Swarm",
        code="SW-INV-1",
        parent_task_id="task-102",
        purpose="Test illegal state change",
        manager_id="emp-mgr-1",
    )

    with pytest.raises(InvalidStateTransitionError):
        swarm.transition_to(SwarmStatus.COMPLETED)


def test_swarm_max_agents_enforced():
    swarm = Swarm(
        id="swarm-003",
        name="Small Swarm",
        code="SW-SML-1",
        parent_task_id="task-103",
        purpose="Test max agents capacity limit",
        manager_id="emp-mgr-1",
        max_agents=2,
    )

    m1 = SwarmMember(id="sm-1", swarm_id=swarm.id, employee_id="emp-1", agent_id="agent-1", role="Coder", capability="code_generation")
    m2 = SwarmMember(id="sm-2", swarm_id=swarm.id, employee_id="emp-2", agent_id="agent-2", role="Tester", capability="testing")
    m3 = SwarmMember(id="sm-3", swarm_id=swarm.id, employee_id="emp-3", agent_id="agent-3", role="Reviewer", capability="code_review")

    swarm.add_member(m1)
    swarm.add_member(m2)

    with pytest.raises(SwarmValidationError):
        swarm.add_member(m3)


def test_swarm_budget_usage_and_exhaustion():
    budget = SwarmBudget(
        swarm_id="swarm-004",
        max_execution_time_seconds=100,
        max_model_cost=10.0,
        max_tool_calls=5,
        max_tokens=1000,
        max_retries=2,
    )
    assert not budget.is_exhausted()

    budget.record_usage(duration_seconds=50, model_cost=2.5, tool_calls=2, tokens=300)
    assert not budget.is_exhausted()

    budget.record_usage(tool_calls=4)  # Total 6 tool calls > max 5
    assert budget.is_exhausted()
