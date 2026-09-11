"""
Configuration-Driven Employee Loader.
Parses YAML / JSON employee definitions into Domain Employee entities.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from src.domain.employee import (
    Employee,
    EmployeeCapability,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)


class EmployeeSkillSchema(BaseModel):
    name: str
    category: str = "general"
    proficiency: SkillProficiency = SkillProficiency.INTERMEDIATE


class EmployeeCapabilitySchema(BaseModel):
    name: str
    description: str = ""


class EmployeeDefinitionSchema(BaseModel):
    id: str
    employee_code: str
    name: str
    title: str
    role: str
    agent_id: str
    department_id: str | None = None
    manager_id: str | None = None
    responsibilities: list[str] = Field(default_factory=list)
    skills: list[EmployeeSkillSchema] = Field(default_factory=list)
    capabilities: list[EmployeeCapabilitySchema] = Field(default_factory=list)
    status: EmployeeStatus = EmployeeStatus.INACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)


def parse_employee_definition(data: dict[str, Any]) -> Employee:
    """Parse raw dictionary data into a Domain Employee entity."""
    emp_data = data.get("employee", data)
    schema = EmployeeDefinitionSchema.model_validate(emp_data)

    skills = [
        EmployeeSkill(
            name=s.name,
            category=s.category,
            proficiency=s.proficiency,
        )
        for s in schema.skills
    ]
    capabilities = [
        EmployeeCapability(
            name=c.name,
            description=c.description,
        )
        for c in schema.capabilities
    ]

    return Employee(
        id=schema.id,
        employee_code=schema.employee_code,
        name=schema.name,
        title=schema.title,
        role=schema.role,
        agent_id=schema.agent_id,
        department_id=schema.department_id,
        manager_id=schema.manager_id,
        responsibilities=schema.responsibilities,
        skills=skills,
        capabilities=capabilities,
        status=schema.status,
        metadata=schema.metadata,
    )


def load_employee_from_yaml(yaml_path: str | Path) -> Employee:
    """Load and parse an Employee entity from a YAML definition file."""
    path = Path(yaml_path)
    if not path.is_file():
        raise FileNotFoundError(f"Employee configuration file not found at '{yaml_path}'")

    with open(path, encoding="utf-8") as f:
        content = yaml.safe_load(f)

    if not isinstance(content, dict):
        raise ValueError(f"Invalid YAML configuration content in '{yaml_path}'")

    return parse_employee_definition(content)
