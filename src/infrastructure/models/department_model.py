"""
SQLAlchemy ORM Models for Phase 14 Department persistence and domain mapping.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.department import (
    Department,
    DepartmentHandoff,
    DepartmentHealth,
    DepartmentMetrics,
    DepartmentRequest,
    DepartmentRequestPriority,
    DepartmentRequestStatus,
    DepartmentServiceContract,
    DepartmentStatus,
)
from src.infrastructure.database import Base


class DepartmentModel(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    purpose: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    responsibilities: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    capabilities: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    manager_employee_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    parent_department_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class DepartmentRequestModel(Base):
    __tablename__ = "department_requests"

    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    requester_department_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    receiving_department_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    requester_employee_id: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    requested_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REQUESTED", index=True)
    accountable_manager_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    delivery_owner_employee_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_completion_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    required_capabilities: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    related_objective_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    related_project_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    governance_request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class DepartmentHandoffModel(Base):
    __tablename__ = "department_handoffs"

    handoff_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sender_department_id: Mapped[str] = mapped_column(String(64), nullable=False)
    receiving_department_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_employee_id: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    receiver_employee_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    artifact_ids: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING_VERIFICATION")
    verification_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class DepartmentServiceContractModel(Base):
    __tablename__ = "department_service_contracts"

    contract_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_department_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    consumer_department_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    service_type: Mapped[str] = mapped_column(String(128), nullable=False)
    required_input_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    expected_output_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    acceptance_criteria: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    sla_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=86400)
    requires_governance_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class DepartmentMetricsModel(Base):
    __tablename__ = "department_metrics"

    department_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    active_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    blocked_task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    incoming_request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outgoing_request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verification_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recovery_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    escalation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    health: Mapped[str] = mapped_column(String(32), nullable=False, default="HEALTHY")
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
        purpose=model.purpose,
        status=DepartmentStatus(model.status),
        responsibilities=list(model.responsibilities or []),
        capabilities=list(model.capabilities or []),
        manager_employee_id=model.manager_employee_id,
        parent_department_id=model.parent_department_id,
        metadata=dict(model.metadata_json or {}),
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
        purpose=dept.purpose,
        status=dept.status.value if hasattr(dept.status, "value") else str(dept.status),
        responsibilities=dept.responsibilities,
        capabilities=dept.capabilities,
        manager_employee_id=dept.manager_employee_id,
        parent_department_id=dept.parent_department_id,
        metadata_json=dept.metadata,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )
