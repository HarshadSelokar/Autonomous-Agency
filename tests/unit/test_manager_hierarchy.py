"""
Unit tests for Manager Role Capabilities and Hierarchy Cycle Detection.
"""

from unittest.mock import AsyncMock

import pytest

from src.application.employee_service import EmployeeService
from src.domain.employee import Employee, EmployeeCapability, EmployeeSkill, EmployeeStatus
from src.domain.exceptions import EmployeeValidationError


def test_employee_is_manager_by_title_and_role() -> None:
    emp = Employee(
        id="emp_mgr_01",
        employee_code="EMP-MGR-01",
        name="Bob Manager",
        title="Engineering Manager",
        role="engineering_manager",
        agent_id="agent_001",
        status=EmployeeStatus.ACTIVE,
    )
    assert emp.is_manager()
    assert emp.possesses_capability("planning") is False


def test_employee_is_manager_by_capability() -> None:
    emp = Employee(
        id="emp_mgr_02",
        employee_code="EMP-MGR-02",
        name="Alice Tech Lead",
        title="Senior Architect",
        role="architect",
        agent_id="agent_002",
        capabilities=[
            EmployeeCapability(name="planning", description="Project planning"),
            EmployeeCapability(name="task_decomposition", description="Decompose tasks"),
        ],
        skills=[EmployeeSkill(name="python")],
        status=EmployeeStatus.ACTIVE,
    )
    assert emp.is_manager()
    assert emp.possesses_capability("planning")
    assert emp.possesses_capability("python")
    assert emp.possesses_capability("rust") is False


def test_non_manager_employee() -> None:
    emp = Employee(
        id="emp_dev_01",
        employee_code="EMP-DEV-01",
        name="Charlie Dev",
        title="Software Engineer",
        role="software_engineer",
        agent_id="agent_003",
        status=EmployeeStatus.ACTIVE,
    )
    assert not emp.is_manager()


@pytest.mark.asyncio
async def test_circular_manager_hierarchy_detection_2_nodes() -> None:
    mock_emp_repo = AsyncMock()
    mock_agent_repo = AsyncMock()
    mock_engine = AsyncMock()

    emp1 = Employee(
        id="emp_1",
        employee_code="E-1",
        name="Emp 1",
        title="Manager 1",
        role="manager",
        agent_id="ag_1",
        manager_id="emp_2",
    )
    emp2 = Employee(
        id="emp_2",
        employee_code="E-2",
        name="Emp 2",
        title="Manager 2",
        role="manager",
        agent_id="ag_2",
        manager_id=None,
    )

    def get_by_id_side_effect(emp_id: str) -> Employee | None:
        if emp_id == "emp_1":
            return emp1
        if emp_id == "emp_2":
            return emp2
        return None

    mock_emp_repo.get_by_id.side_effect = get_by_id_side_effect

    service = EmployeeService(
        employee_repo=mock_emp_repo,
        agent_repo=mock_agent_repo,
        execution_engine=mock_engine,
    )

    # Attempt setting emp2.manager_id = "emp_1" (creating emp1 -> emp2 -> emp1 cycle)
    with pytest.raises(EmployeeValidationError) as exc:
        await service.update_manager("emp_2", "emp_1")

    assert "Circular manager hierarchy detected" in str(exc.value)


@pytest.mark.asyncio
async def test_circular_manager_hierarchy_detection_3_nodes() -> None:
    mock_emp_repo = AsyncMock()
    mock_agent_repo = AsyncMock()
    mock_engine = AsyncMock()

    emp1 = Employee(
        id="emp_1",
        employee_code="E-1",
        name="E1",
        title="MGR",
        role="mgr",
        agent_id="ag_1",
        manager_id="emp_2",
    )
    emp2 = Employee(
        id="emp_2",
        employee_code="E-2",
        name="E2",
        title="MGR",
        role="mgr",
        agent_id="ag_2",
        manager_id="emp_3",
    )
    emp3 = Employee(
        id="emp_3",
        employee_code="E-3",
        name="E3",
        title="MGR",
        role="mgr",
        agent_id="ag_3",
        manager_id=None,
    )

    def get_by_id_side_effect(emp_id: str) -> Employee | None:
        if emp_id == "emp_1":
            return emp1
        if emp_id == "emp_2":
            return emp2
        if emp_id == "emp_3":
            return emp3
        return None

    mock_emp_repo.get_by_id.side_effect = get_by_id_side_effect

    service = EmployeeService(
        employee_repo=mock_emp_repo,
        agent_repo=mock_agent_repo,
        execution_engine=mock_engine,
    )

    # Attempt setting emp3.manager_id = "emp_1" (creating emp1 -> emp2 -> emp3 -> emp1 cycle)
    with pytest.raises(EmployeeValidationError) as exc:
        await service.update_manager("emp_3", "emp_1")

    assert "Circular manager hierarchy detected" in str(exc.value)
