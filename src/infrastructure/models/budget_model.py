"""
SQLAlchemy ORM Models for Budget and Cost Persistence (Phase 35).
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.budget import Budget, BudgetType, CostRecord
from src.infrastructure.database import Base


class ResourceBudgetModel(Base):
    __tablename__ = "resource_budgets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    budget_type: Mapped[str] = mapped_column(String(32), nullable=False, default="COST", index=True)
    allocated_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    used_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reserved_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="USD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class CostRecordModel(Base):
    __tablename__ = "cost_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    tokens_prompt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_completion: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def budget_model_to_domain(model: ResourceBudgetModel) -> Budget:
    return Budget(
        id=model.id,
        tenant_id=model.tenant_id,
        project_id=model.project_id,
        budget_type=BudgetType(model.budget_type),
        allocated_amount=model.allocated_amount,
        used_amount=model.used_amount,
        reserved_amount=model.reserved_amount,
        currency=model.currency,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def budget_domain_to_model(domain: Budget) -> ResourceBudgetModel:
    return ResourceBudgetModel(
        id=domain.id,
        tenant_id=domain.tenant_id,
        project_id=domain.project_id,
        budget_type=domain.budget_type.value if isinstance(domain.budget_type, BudgetType) else str(domain.budget_type),
        allocated_amount=domain.allocated_amount,
        used_amount=domain.used_amount,
        reserved_amount=domain.reserved_amount,
        currency=domain.currency,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
