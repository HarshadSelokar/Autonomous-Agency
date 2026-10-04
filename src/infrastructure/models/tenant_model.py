"""
SQLAlchemy ORM Model for Tenant persistence and domain mapping (Phase 32).
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.tenant import Tenant, TenantConfiguration, TenantPlan, TenantStatus
from src.infrastructure.database import Base


class TenantModel(Base):
    __tablename__ = "tenants"
    # A tenant row is owned by itself: tenant_id is set to its own id on insert
    __tenant_is_self__ = True

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE", index=True)
    plan: Mapped[str] = mapped_column(String(32), nullable=False, default="FREE", index=True)
    configuration_json: Mapped[dict[str, Any]] = mapped_column("configuration", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def tenant_model_to_domain(model: TenantModel) -> Tenant:
    config_dict = model.configuration_json or {}
    config = TenantConfiguration(
        max_users=config_dict.get("max_users", 100),
        max_projects=config_dict.get("max_projects", 50),
        max_workflows=config_dict.get("max_workflows", 20),
        allowed_providers=config_dict.get("allowed_providers", ["groq", "fake"]),
        custom_settings=config_dict.get("custom_settings", {}),
    )
    return Tenant(
        id=model.id,
        name=model.name,
        slug=model.slug,
        status=TenantStatus(model.status),
        plan=TenantPlan(model.plan),
        configuration=config,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def tenant_domain_to_model(domain: Tenant) -> TenantModel:
    config_dict = {
        "max_users": domain.configuration.max_users,
        "max_projects": domain.configuration.max_projects,
        "max_workflows": domain.configuration.max_workflows,
        "allowed_providers": domain.configuration.allowed_providers,
        "custom_settings": domain.configuration.custom_settings,
    }
    return TenantModel(
        id=domain.id,
        name=domain.name,
        slug=domain.slug,
        status=domain.status.value if isinstance(domain.status, TenantStatus) else str(domain.status),
        plan=domain.plan.value if isinstance(domain.plan, TenantPlan) else str(domain.plan),
        configuration_json=config_dict,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
    )
