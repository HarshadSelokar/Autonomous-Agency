"""
Unit tests for Agent domain model and state machine transitions.
"""

import pytest

from src.domain.agent import (
    Agent,
    AgentState,
    ModelConfiguration,
    PermissionProfile,
    VerificationPolicy,
)
from src.domain.exceptions import InvalidStateTransitionError


def test_agent_creation() -> None:
    agent = Agent(
        id="employee_001",
        name="Alice",
        role="Researcher",
        responsibilities=["Research AI architectures", "Summarize findings"],
        capabilities=["research", "analysis"],
        model_configuration=ModelConfiguration(provider="groq", model="llama-3.3-70b-versatile"),
        permission_profile=PermissionProfile(permissions=["read_docs"]),
        verification_policy=VerificationPolicy(required=True, verifier_role="Lead Architect"),
    )

    assert agent.id == "employee_001"
    assert agent.name == "Alice"
    assert agent.current_state == AgentState.IDLE
    assert agent.permission_profile.has_permission("read_docs")
    assert not agent.permission_profile.has_permission("write_code")


def test_valid_agent_state_transitions() -> None:
    agent = Agent(id="emp_002", name="Bob", role="Engineer")

    # IDLE -> READY
    agent.transition_to(AgentState.READY)
    assert agent.current_state == AgentState.READY

    # READY -> RUNNING
    agent.transition_to(AgentState.RUNNING)
    assert agent.current_state == AgentState.RUNNING

    # RUNNING -> WAITING
    agent.transition_to(AgentState.WAITING)
    assert agent.current_state == AgentState.WAITING

    # WAITING -> RUNNING
    agent.transition_to(AgentState.RUNNING)
    assert agent.current_state == AgentState.RUNNING

    # RUNNING -> COMPLETED
    agent.transition_to(AgentState.COMPLETED)
    assert agent.current_state == AgentState.COMPLETED

    # COMPLETED -> READY
    agent.transition_to(AgentState.READY)
    assert agent.current_state == AgentState.READY


def test_invalid_agent_state_transition_raises_error() -> None:
    agent = Agent(id="emp_003", name="Charlie", role="Tester")

    # Attempt IDLE -> RUNNING directly (invalid: must go IDLE -> READY first)
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        agent.transition_to(AgentState.RUNNING)

    assert "cannot transition from 'IDLE' to 'RUNNING'" in str(exc_info.value)
    assert agent.current_state == AgentState.IDLE


def test_failed_agent_state_transition_and_recovery() -> None:
    agent = Agent(id="emp_004", name="Dave", role="DevOps")

    agent.transition_to(AgentState.READY)
    agent.transition_to(AgentState.RUNNING)

    # RUNNING -> FAILED
    agent.transition_to(AgentState.FAILED)
    assert agent.current_state == AgentState.FAILED

    # FAILED -> READY (recovery)
    agent.transition_to(AgentState.READY)
    assert agent.current_state == AgentState.READY
