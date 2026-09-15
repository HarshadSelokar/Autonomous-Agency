"""SQLAlchemy ORM Model for Department persistence and domain mapping for Phase 14."""

import json
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.department import Department, DepartmentStatus
from src.infrastructure.database import Base


class DepartmentModel(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    purpose: Mapped[str] = mapped_column(Text, nullable=False, default="")
    manager_employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_department_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capabilities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    responsibilities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    policies_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def department_model_to_domain(model: DepartmentModel) -> Department:
    """Map SQLAlchemy DepartmentModel to pure Domain Department entity."""
    return Department(
        id=model.id,
        name=model.name,
        code=model.code,
        description=model.description,
        status=DepartmentStatus(model.status),
        purpose=model.purpose or "",
        manager_employee_id=model.manager_employee_id,
        parent_department_id=model.parent_department_id,
        capabilities=json.loads(model.capabilities_json) if model.capabilities_json else [],
        responsibilities=json.loads(model.responsibilities_json) if model.responsibilities_json else [],
        policies=json.loads(model.policies_json) if model.policies_json else [],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def department_domain_to_model(dept: Department) -> DepartmentModel:
    """Map pure Domain Department entity to SQLAlchemy DepartmentModel."""
    return DepartmentModel(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        status=dept.status.value if hasattr(dept.status, "value") else str(dept.status),
        purpose=dept.purpose,
        manager_employee_id=dept.manager_employee_id,
        parent_department_id=dept.parent_department_id,
        capabilities_json=json.dumps(dept.capabilities),
        responsibilities_json=json.dumps(dept.responsibilities),
        policies_json=json.dumps(dept.policies),
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )
