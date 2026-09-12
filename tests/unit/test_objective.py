"""
Unit tests for Objective domain entity and state machine transitions.
"""

import pytest

from src.domain.exceptions import InvalidStateTransitionError, ObjectiveValidationError
from src.domain.objective import Objective, ObjectiveStatus


def test_objective_creation_and_validation() -> None:
    obj = Objective(
        id="obj_001",
        title="Build CSV analytics tool",
        description="Develop a Python web application that parses CSVs and visualizes trends.",
        requester="CEO",
        priority="high",
        constraints=["python3.11", "fastapi"],
    )

    assert obj.id == "obj_001"
    assert obj.status == ObjectiveStatus.RECEIVED
    assert obj.priority == "high"
    assert len(obj.constraints) == 2


def test_objective_validation_errors() -> None:
    with pytest.raises(ObjectiveValidationError) as exc:
        Objective(id="", title="Title", description="Desc", requester="Req")
    assert "Objective ID cannot be empty" in str(exc.value)

    with pytest.raises(ObjectiveValidationError) as exc:
        Objective(id="obj_1", title="", description="Desc", requester="Req")
    assert "Objective title cannot be empty" in str(exc.value)

    with pytest.raises(ObjectiveValidationError) as exc:
        Objective(id="obj_1", title="Title", description="", requester="Req")
    assert "Objective description cannot be empty" in str(exc.value)

    with pytest.raises(ObjectiveValidationError) as exc:
        Objective(id="obj_1", title="Title", description="Desc", requester="")
    assert "Objective requester cannot be empty" in str(exc.value)


def test_valid_objective_transitions() -> None:
    obj = Objective(
        id="obj_002",
        title="Test Transitions",
        description="Testing state machine",
        requester="User",
    )

    # RECEIVED -> PLANNING
    obj.transition_to(ObjectiveStatus.PLANNING)
    assert obj.status == ObjectiveStatus.PLANNING

    # PLANNING -> PLANNED
    obj.transition_to(ObjectiveStatus.PLANNED)
    assert obj.status == ObjectiveStatus.PLANNED

    # PLANNED -> EXECUTING
    obj.transition_to(ObjectiveStatus.EXECUTING)
    assert obj.status == ObjectiveStatus.EXECUTING

    # EXECUTING -> REVIEWING
    obj.transition_to(ObjectiveStatus.REVIEWING)
    assert obj.status == ObjectiveStatus.REVIEWING

    # REVIEWING -> COMPLETED
    obj.transition_to(ObjectiveStatus.COMPLETED)
    assert obj.status == ObjectiveStatus.COMPLETED


def test_invalid_objective_transition_raises_error() -> None:
    obj = Objective(
        id="obj_003",
        title="Terminal Objective",
        description="Completed objective",
        requester="User",
        status=ObjectiveStatus.COMPLETED,
    )

    with pytest.raises(InvalidStateTransitionError) as exc:
        obj.transition_to(ObjectiveStatus.EXECUTING)

    assert "cannot transition from 'COMPLETED' to 'EXECUTING'" in str(exc.value)
