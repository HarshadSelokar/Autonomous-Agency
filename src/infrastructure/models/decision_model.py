"""
SQLAlchemy ORM Models for Organizational Decision persistence, domain mapping, and audit logging.
Supports both evolved Phase 6 Decision entity and Phase 3 ManagerDecision backward compatibility.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.decision import (
    Decision,
    DecisionProvenance,
    DecisionStatus,
    DecisionType,
)
from src.infrastructure.database import Base


class DecisionModel(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    question: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_maker_employee_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    decision_type: Mapped[str] = mapped_column(String(64), nullable=False)
    approving_authority_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    chosen_option: Mapped[str | None] = mapped_column(String(512), nullable=True)
    alternatives_json: Mapped[list[str]] = mapped_column("alternatives", JSON, nullable=False, default=list)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    consequences_json: Mapped[list[str]] = mapped_column("consequences", JSON, nullable=False, default=list)
    evidence_json: Mapped[list[str]] = mapped_column("evidence", JSON, nullable=False, default=list)
    meeting_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    objective_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("objectives.id", ondelete="SET NULL"), nullable=True, index=True
    )
    plan_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    task_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    previous_decision_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("decisions.id", ondelete="SET NULL"), nullable=True
    )
    provenance: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    audits: Mapped[list["DecisionAuditModel"]] = relationship(
        "DecisionAuditModel", back_populates="decision", cascade="all, delete-orphan", lazy="joined"
    )


class DecisionAuditModel(Base):
    __tablename__ = "decision_audits"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    decision_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("decisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_employee_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    previous_status: Mapped[str] = mapped_column(String(64), nullable=False)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    decision: Mapped["DecisionModel"] = relationship("DecisionModel", back_populates="audits")


class ManagerDecisionModel(Base):
    """Phase 3 legacy table ORM model preserved for backward compatibility."""

    __tablename__ = "manager_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    manager_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    objective_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("objectives.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reasoning_summary: Mapped[str] = mapped_column(String(2048), nullable=False)
    selected_action: Mapped[str] = mapped_column(String(512), nullable=False)
    alternatives_json: Mapped[list[str]] = mapped_column("alternatives", JSON, nullable=False, default=list)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


def decision_model_to_domain(model: DecisionModel) -> Decision:
    return Decision(
        id=model.id,
        title=model.title,
        question=model.question,
        description=model.description,
        status=DecisionStatus(model.status),
        decision_maker_employee_id=model.decision_maker_employee_id,
        decision_type=DecisionType(model.decision_type),
        approving_authority_role=model.approving_authority_role,
        chosen_option=model.chosen_option,
        alternatives=list(model.alternatives_json or []),
        rationale=model.rationale,
        consequences=list(model.consequences_json or []),
        evidence=list(model.evidence_json or []),
        meeting_id=model.meeting_id,
        objective_id=model.objective_id,
        plan_id=model.plan_id,
        task_id=model.task_id,
        previous_decision_id=model.previous_decision_id,
        provenance=DecisionProvenance(model.provenance),
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        approved_at=model.approved_at,
        updated_at=model.updated_at,
    )


def decision_domain_to_model(domain: Decision) -> DecisionModel:
    return DecisionModel(
        id=domain.id,
        title=domain.title,
        question=domain.question,
        description=domain.description,
        status=domain.status.value,
        decision_maker_employee_id=domain.decision_maker_employee_id,
        decision_type=domain.decision_type.value,
        approving_authority_role=domain.approving_authority_role,
        chosen_option=domain.chosen_option,
        alternatives_json=domain.alternatives,
        rationale=domain.rationale,
        consequences_json=domain.consequences,
        evidence_json=domain.evidence,
        meeting_id=domain.meeting_id,
        objective_id=domain.objective_id,
        plan_id=domain.plan_id,
        task_id=domain.task_id,
        previous_decision_id=domain.previous_decision_id,
        provenance=domain.provenance.value,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        approved_at=domain.approved_at,
        updated_at=domain.updated_at,
    )
