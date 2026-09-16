"""
SQLAlchemy ORM Models for Phase 8 Tools, Executions, Approvals, and Evidence.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.tool import (
    PermissionMode,
    ToolCapability,
    ToolCategory,
    ToolDefinition,
    ToolRiskLevel,
    ToolStatus,
)
from src.infrastructure.database import Base


class ToolModel(Base):
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="INTEGRATION")
    capabilities: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    input_schema: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    output_schema: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="LOW")
    permission_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="AUTO")
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False, default="internal")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=30.0)
    retry_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    is_idempotent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ToolExecutionModel(Base):
    __tablename__ = "tool_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tool_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tool_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    approval_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REQUESTED", index=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ToolApprovalModel(Base):
    __tablename__ = "tool_approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tool_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    requester_employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    approver_employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ToolEvidenceModel(Base):
    __tablename__ = "tool_evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tool_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    approval_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


def tool_domain_to_model(domain: ToolDefinition) -> ToolModel:
    return ToolModel(
        id=domain.id,
        name=domain.name,
        description=domain.description,
        version=domain.version,
        category=domain.category.value,
        capabilities=[c.value for c in domain.capabilities],
        input_schema=domain.input_schema,
        output_schema=domain.output_schema,
        risk_level=domain.risk_level.value,
        permission_mode=domain.permission_mode.value,
        provider_name=domain.provider_name,
        status=domain.status.value,
        timeout_seconds=domain.timeout_seconds,
        retry_limit=domain.retry_limit,
        is_idempotent=domain.is_idempotent,
        extra_metadata=domain.metadata,
        created_at=domain.created_at if hasattr(domain, "created_at") else datetime.now(UTC),
        updated_at=domain.updated_at if hasattr(domain, "updated_at") else datetime.now(UTC),
    )


def tool_model_to_domain(model: ToolModel) -> ToolDefinition:
    caps = [ToolCapability(c) for c in (model.capabilities or [])]
    return ToolDefinition(
        id=model.id,
        name=model.name,
        description=model.description,
        version=model.version,
        category=ToolCategory(model.category),
        capabilities=caps,
        input_schema=model.input_schema or {},
        output_schema=model.output_schema or {},
        risk_level=ToolRiskLevel(model.risk_level),
        permission_mode=PermissionMode(model.permission_mode),
        provider_name=model.provider_name,
        status=ToolStatus(model.status),
        timeout_seconds=model.timeout_seconds,
        retry_limit=model.retry_limit,
        is_idempotent=model.is_idempotent,
        metadata=model.extra_metadata or {},
    )
