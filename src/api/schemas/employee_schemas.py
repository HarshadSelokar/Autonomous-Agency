"""
Pydantic schemas for Employee API requests and responses.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.employee import (
    Employee,
    EmployeeCapability,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)


class EmployeeSkillSchema(BaseModel):
    name: str
    category: str
    proficiency: SkillProficiency = SkillProficiency.INTERMEDIATE

    def to_domain(self) -> EmployeeSkill:
        return EmployeeSkill(
            name=self.name,
            category=self.category,
            proficiency=self.proficiency,
        )

    @classmethod
    def from_domain(cls, skill: EmployeeSkill) -> "EmployeeSkillSchema":
        return cls(
            name=skill.name,
            category=skill.category,
            proficiency=skill.proficiency,
        )


class EmployeeCapabilitySchema(BaseModel):
    name: str
    description: str = ""

    def to_domain(self) -> EmployeeCapability:
        return EmployeeCapability(
            name=self.name,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, capability: EmployeeCapability) -> "EmployeeCapabilitySchema":
        return cls(
            name=capability.name,
            description=capability.description,
        )


class CreateEmployeeRequest(BaseModel):
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
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateEmployeeRequest(BaseModel):
    manager_id: str | None = None
    department_id: str | None = None


class UpdateEmployeeStatusRequest(BaseModel):
    status: EmployeeStatus


class ExecuteEmployeeWorkRequest(BaseModel):
    objective: str
    task_id: str | None = None
    response_schema: dict[str, Any] | None = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_code: str
    name: str
    title: str
    role: str
    agent_id: str
    department_id: str | None
    manager_id: str | None
    status: EmployeeStatus
    responsibilities: list[str]
    skills: list[EmployeeSkillSchema]
    capabilities: list[EmployeeCapabilitySchema]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, emp: Employee) -> "EmployeeResponse":
        return cls(
            id=emp.id,
            employee_code=emp.employee_code,
            name=emp.name,
            title=emp.title,
            role=emp.role,
            agent_id=emp.agent_id,
            department_id=emp.department_id,
            manager_id=emp.manager_id,
            status=emp.status,
            responsibilities=emp.responsibilities,
            skills=[EmployeeSkillSchema.from_domain(s) for s in emp.skills],
            capabilities=[EmployeeCapabilitySchema.from_domain(c) for c in emp.capabilities],
            metadata=emp.metadata,
            created_at=emp.created_at,
            updated_at=emp.updated_at,
        )
