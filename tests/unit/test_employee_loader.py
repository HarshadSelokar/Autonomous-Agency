"""
Unit tests for configuration-driven Employee loader.
"""

from pathlib import Path

from src.application.employee_loader import load_employee_from_yaml, parse_employee_definition
from src.domain.employee import EmployeeStatus, SkillProficiency


def test_parse_employee_definition_dict() -> None:
    raw_data = {
        "employee": {
            "id": "emp_dict_01",
            "employee_code": "EMP-D1",
            "name": "Dict Employee",
            "title": "Analyst",
            "role": "analyst",
            "agent_id": "agent_dict_01",
            "responsibilities": ["Analyze metrics"],
            "skills": [
                {"name": "sql", "category": "database", "proficiency": "advanced"}
            ],
            "capabilities": [
                {"name": "analytics", "description": "Data analytics"}
            ],
            "status": "ACTIVE",
        }
    }

    emp = parse_employee_definition(raw_data)
    assert emp.id == "emp_dict_01"
    assert emp.name == "Dict Employee"
    assert emp.agent_id == "agent_dict_01"
    assert emp.skills[0].proficiency == SkillProficiency.ADVANCED
    assert emp.status == EmployeeStatus.ACTIVE


def test_load_sample_alice_researcher_yaml() -> None:
    path = Path("config/employees/alice_researcher.yaml")
    emp = load_employee_from_yaml(path)

    assert emp.id == "alice_researcher_001"
    assert emp.employee_code == "EMP-001"
    assert emp.name == "Alice Smith"
    assert emp.role == "researcher"
    assert emp.agent_id == "researcher_001"
    assert emp.status == EmployeeStatus.ACTIVE
    assert len(emp.skills) == 2
