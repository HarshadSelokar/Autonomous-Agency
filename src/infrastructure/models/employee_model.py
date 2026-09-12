"""
SQLAlchemy ORM Model for Employee persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.employee import (
    Employee,
    EmployeeCapability,
    EmployeeSkill,
    EmployeeStatus,
    SkillProficiency,
)
from src.infrastructure.database import Base


class EmployeeModel(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    department_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    manager_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    responsibilities: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    skills_json: Mapped[list[dict[str, Any]]] = mapped_column(
        "skills", JSON, nullable=False, default=list
    )
    capabilities_json: Mapped[list[dict[str, Any]]] = mapped_column(
        "capabilities", JSON, nullable=False, default=list
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=EmployeeStatus.INACTIVE.value, index=True
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def employee_model_to_domain(model: EmployeeModel) -> Employee:
    """Map SQLAlchemy EmployeeModel to pure Domain Employee entity."""
    skills = [
        EmployeeSkill(
            name=s.get("name", ""),
            category=s.get("category", "general"),
            proficiency=SkillProficiency(s.get("proficiency", "intermediate")),
        )
        for s in (model.skills_json or [])
    ]
    capabilities = [
        EmployeeCapability(
            name=c.get("name", ""),
            description=c.get("description", ""),
        )
        for c in (model.capabilities_json or [])
    ]

    return Employee(
        id=model.id,
        employee_code=model.employee_code,
        name=model.name,
        title=model.title,
        role=model.role,
        agent_id=model.agent_id,
        department_id=model.department_id,
        manager_id=model.manager_id,
        responsibilities=list(model.responsibilities or []),
        skills=skills,
        capabilities=capabilities,
        status=EmployeeStatus(model.status),
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def employee_domain_to_model(employee: Employee) -> EmployeeModel:
    """Map pure Domain Employee entity to SQLAlchemy EmployeeModel."""
    skills_json = [
        {
            "name": s.name,
            "category": s.category,
            "proficiency": s.proficiency.value,
        }
        for s in employee.skills
    ]
    capabilities_json = [
        {
            "name": c.name,
            "description": c.description,
        }
        for c in employee.capabilities
    ]

    return EmployeeModel(
        id=employee.id,
        employee_code=employee.employee_code,
        name=employee.name,
        title=employee.title,
        role=employee.role,
        agent_id=employee.agent_id,
        department_id=employee.department_id,
        manager_id=employee.manager_id,
        responsibilities=employee.responsibilities,
        skills_json=skills_json,
        capabilities_json=capabilities_json,
        status=employee.status.value,
        metadata_json=employee.metadata,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )
