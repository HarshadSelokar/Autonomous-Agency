"""
Unit tests for Employee domain model and lifecycle state machine.
"""

import pytest

from src.domain.employee import (
    Employee,
    EmployeeCapability,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)
from src.domain.exceptions import EmployeeValidationError, InvalidStateTransitionError


def test_employee_creation_and_validation() -> None:
    emp = Employee(
        id="emp_001",
        employee_code="EMP-001",
        name="Alice Smith",
        title="Senior AI Researcher",
        role="researcher",
        agent_id="agent_001",
        department_id="dept_research",
        manager_id="emp_mgr_01",
        responsibilities=["Research AI systems", "Write reports"],
        skills=[
            EmployeeSkill(
                name="python", category="programming", proficiency=SkillProficiency.EXPERT
            ),
            EmployeeSkill(
                name="postgresql", category="database", proficiency=SkillProficiency.ADVANCED
            ),
        ],
        capabilities=[
            EmployeeCapability(name="technical_research", description="Conduct deep research"),
        ],
        status=EmployeeStatus.INACTIVE,
    )

    assert emp.id == "emp_001"
    assert emp.name == "Alice Smith"
    assert emp.agent_id == "agent_001"
    assert emp.skills[0].name == "python"
    assert emp.skills[0].proficiency == SkillProficiency.EXPERT
    assert not emp.is_executable()


def test_employee_self_manager_raises_validation_error() -> None:
    with pytest.raises(EmployeeValidationError) as exc:
        Employee(
            id="emp_002",
            employee_code="EMP-002",
            name="Self Manager",
            title="Manager",
            role="manager",
            agent_id="agent_002",
            manager_id="emp_002",  # Self manager!
        )

    assert "cannot be assigned as their own manager" in str(exc.value)


def test_employee_missing_agent_raises_validation_error() -> None:
    with pytest.raises(EmployeeValidationError) as exc:
        Employee(
            id="emp_003",
            employee_code="EMP-003",
            name="No Agent",
            title="Dev",
            role="developer",
            agent_id="",  # Missing agent!
        )

    assert "must reference an associated Agent ID" in str(exc.value)


def test_valid_employee_lifecycle_transitions() -> None:
    emp = Employee(
        id="emp_004",
        employee_code="EMP-004",
        name="Bob Worker",
        title="Software Engineer",
        role="software_engineer",
        agent_id="agent_004",
        status=EmployeeStatus.INACTIVE,
    )

    # INACTIVE -> ACTIVE
    emp.transition_to(EmployeeStatus.ACTIVE)
    assert emp.status == EmployeeStatus.ACTIVE
    assert emp.is_executable()

    # ACTIVE -> ON_LEAVE
    emp.transition_to(EmployeeStatus.ON_LEAVE)
    assert emp.status == EmployeeStatus.ON_LEAVE
    assert not emp.is_executable()

    # ON_LEAVE -> ACTIVE
    emp.transition_to(EmployeeStatus.ACTIVE)
    assert emp.status == EmployeeStatus.ACTIVE

    # ACTIVE -> SUSPENDED
    emp.transition_to(EmployeeStatus.SUSPENDED)
    assert emp.status == EmployeeStatus.SUSPENDED
    assert not emp.is_executable()

    # SUSPENDED -> ACTIVE
    emp.transition_to(EmployeeStatus.ACTIVE)
    assert emp.status == EmployeeStatus.ACTIVE

    # ACTIVE -> TERMINATED
    emp.transition_to(EmployeeStatus.TERMINATED)
    assert emp.status == EmployeeStatus.TERMINATED
    assert not emp.is_executable()


def test_invalid_employee_state_transition_raises_error() -> None:
    emp = Employee(
        id="emp_005",
        employee_code="EMP-005",
        name="Charlie",
        title="Dev",
        role="developer",
        agent_id="agent_005",
        status=EmployeeStatus.TERMINATED,
    )

    # Attempt TERMINATED -> ACTIVE (invalid transition from terminal state)
    with pytest.raises(InvalidStateTransitionError) as exc:
        emp.transition_to(EmployeeStatus.ACTIVE)

    assert "cannot transition from 'TERMINATED' to 'ACTIVE'" in str(exc.value)
    assert emp.status == EmployeeStatus.TERMINATED
