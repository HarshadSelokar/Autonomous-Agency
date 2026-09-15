"""
SQLAlchemy ORM Models for Phase 10 Verification & Recovery entities.
"""

from datetime import UTC, datetime
from typing import Any, Optional
from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class VerificationModel(Base):
    __tablename__ = "verifications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    outcome_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommended_recovery: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_human_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_by_actor_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_ids: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ExpectedOutcomeModel(Base):
    __tablename__ = "expected_outcomes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    criteria: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    rules_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    required_evidence_types: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    completion_conditions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    failure_conditions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    policy: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class VerificationEvidenceModel(Base):
    __tablename__ = "verification_evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    workspace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    agent_run_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tool_execution_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    artifact_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    trust_level: Mapped[str] = mapped_column(String(32), nullable=False, default="UNTRUSTED")
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    artifact_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class FailureRecordModel(Base):
    __tablename__ = "failure_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    verification_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="HIGH")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recoverable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    recommended_strategy: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    employee_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    execution_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence_ids: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class RecoveryActionModel(Base):
    __tablename__ = "recovery_actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    failure_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    executed_by: Mapped[str] = mapped_column(String(64), nullable=False, default="SYSTEM")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
