"""
Unit tests for EmployeeSelector capability-based employee selection.
"""

from src.application.employee_selector import EmployeeSelector
from src.domain.employee import Employee, EmployeeCapability, EmployeeSkill, EmployeeStatus


def test_employee_selector_filters_inactive_employees() -> None:
    selector = EmployeeSelector()
    emp_active = Employee(
        id="emp_act",
        employee_code="E-ACT",
        name="Active",
        title="Dev",
        role="dev",
        agent_id="ag1",
        skills=[EmployeeSkill(name="python")],
        status=EmployeeStatus.ACTIVE,
    )
    emp_inactive = Employee(
        id="emp_inact",
        employee_code="E-INACT",
        name="Inactive",
        title="Dev",
        role="dev",
        agent_id="ag2",
        skills=[EmployeeSkill(name="python")],
        status=EmployeeStatus.INACTIVE,
    )

    eligible = selector.find_eligible_employees(
        employees=[emp_active, emp_inactive],
        required_capabilities=["python"],
    )

    assert len(eligible) == 1
    assert eligible[0].id == "emp_act"


def test_employee_selector_capability_matching() -> None:
    selector = EmployeeSelector()
    emp_py = Employee(
        id="emp_py",
        employee_code="E-PY",
        name="Py Dev",
        title="Dev",
        role="dev",
        agent_id="ag1",
        skills=[EmployeeSkill(name="python")],
        status=EmployeeStatus.ACTIVE,
    )
    emp_fullstack = Employee(
        id="emp_fs",
        employee_code="E-FS",
        name="Fullstack Dev",
        title="Dev",
        role="dev",
        agent_id="ag2",
        skills=[EmployeeSkill(name="python"), EmployeeSkill(name="react")],
        capabilities=[EmployeeCapability(name="fastapi")],
        status=EmployeeStatus.ACTIVE,
    )

    # Search for python + fastapi
    eligible = selector.find_eligible_employees(
        employees=[emp_py, emp_fullstack],
        required_capabilities=["python", "fastapi"],
        require_all=True,
    )

    assert len(eligible) == 1
    assert eligible[0].id == "emp_fs"
