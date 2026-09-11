"""
SQLAlchemy ORM Model for Department persistence and domain mapping.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.department import Department
from src.infrastructure.database import Base


class DepartmentModel(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
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
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )
