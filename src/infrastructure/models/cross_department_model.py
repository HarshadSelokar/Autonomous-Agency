"""SQLAlchemy ORM Models for Cross-Department Requests, Handoffs, and Service Contracts."""

import json
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.cross_department import (
    DepartmentHandoff,
    DepartmentPriority,
    DepartmentRequest,
    DepartmentRequestStatus,
    HandoffStatus,
)
from src.infrastructure.database import Base


class DepartmentRequestModel(Base):
    __tablename__ = "department_requests"

    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    requester_department_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    receiving_department_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    requester_employee_id: Mapped[str] = mapped_column(String(64), nullable=False)
    receiving_manager_id: Mapped[str] = mapped_column(String(64), nullable=False)
    delivery_owner_employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    requested_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM")
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    required_capabilities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REQUESTED")
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_objective_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
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
    receiver_department_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_employee_id: Mapped[str] = mapped_column(String(64), nullable=False)
    expected_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    acceptance_criteria_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    verification_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class DepartmentServiceContractModel(Base):
    __tablename__ = "department_service_contracts"

    contract_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_department_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    consumer_department_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    service_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_schema_description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output_description: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_criteria_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    target_sla_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=86400)
    required_approvals_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")


def department_request_model_to_domain(model: DepartmentRequestModel) -> DepartmentRequest:
    return DepartmentRequest(
        request_id=model.request_id,
        requester_department_id=model.requester_department_id,
        receiving_department_id=model.receiving_department_id,
        requester_employee_id=model.requester_employee_id,
        receiving_manager_id=model.receiving_manager_id,
        delivery_owner_employee_id=model.delivery_owner_employee_id,
        purpose=model.purpose,
        requested_outcome=model.requested_outcome,
        priority=DepartmentPriority(model.priority),
        sla_deadline=model.sla_deadline,
        required_capabilities=json.loads(model.required_capabilities_json) if model.required_capabilities_json else [],
        status=DepartmentRequestStatus(model.status),
        rejection_reason=model.rejection_reason,
        related_objective_id=model.related_objective_id,
        related_project_id=model.related_project_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def department_request_domain_to_model(req: DepartmentRequest) -> DepartmentRequestModel:
    return DepartmentRequestModel(
        request_id=req.request_id,
        requester_department_id=req.requester_department_id,
        receiving_department_id=req.receiving_department_id,
        requester_employee_id=req.requester_employee_id,
        receiving_manager_id=req.receiving_manager_id,
        delivery_owner_employee_id=req.delivery_owner_employee_id,
        purpose=req.purpose,
        requested_outcome=req.requested_outcome,
        priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
        sla_deadline=req.sla_deadline,
        required_capabilities_json=json.dumps(req.required_capabilities),
        status=req.status.value if hasattr(req.status, "value") else str(req.status),
        rejection_reason=req.rejection_reason,
        related_objective_id=req.related_objective_id,
        related_project_id=req.related_project_id,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


def department_handoff_model_to_domain(model: DepartmentHandoffModel) -> DepartmentHandoff:
    return DepartmentHandoff(
        handoff_id=model.handoff_id,
        request_id=model.request_id,
        sender_department_id=model.sender_department_id,
        receiver_department_id=model.receiver_department_id,
        sender_employee_id=model.sender_employee_id,
        expected_outcome=model.expected_outcome,
        artifact_ids=json.loads(model.artifact_ids_json) if model.artifact_ids_json else [],
        evidence_ids=json.loads(model.evidence_ids_json) if model.evidence_ids_json else [],
        status=HandoffStatus(model.status),
        acceptance_criteria=json.loads(model.acceptance_criteria_json) if model.acceptance_criteria_json else [],
        verification_id=model.verification_id,
        is_verified=model.is_verified,
        rejection_reason=model.rejection_reason,
        created_at=model.created_at,
    )


def department_handoff_domain_to_model(handoff: DepartmentHandoff) -> DepartmentHandoffModel:
    return DepartmentHandoffModel(
        handoff_id=handoff.handoff_id,
        request_id=handoff.request_id,
        sender_department_id=handoff.sender_department_id,
        receiver_department_id=handoff.receiver_department_id,
        sender_employee_id=handoff.sender_employee_id,
        expected_outcome=handoff.expected_outcome,
        artifact_ids_json=json.dumps(handoff.artifact_ids),
        evidence_ids_json=json.dumps(handoff.evidence_ids),
        status=handoff.status.value if hasattr(handoff.status, "value") else str(handoff.status),
        acceptance_criteria_json=json.dumps(handoff.acceptance_criteria),
        verification_id=handoff.verification_id,
        is_verified=handoff.is_verified,
        rejection_reason=handoff.rejection_reason,
        created_at=handoff.created_at,
    )
