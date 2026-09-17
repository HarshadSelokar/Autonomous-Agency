"""
SQLAlchemy ORM models for Phase 30 Production Hardening, Security, Reliability, DR & Resilience.
"""

from datetime import datetime, timezone, UTC
import json

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.infrastructure.database import Base


class CircuitBreakerModel(Base):
    __tablename__ = "circuit_breakers"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    dependency_name = Column(String(255), nullable=False, index=True)
    state = Column(String(64), nullable=False, default="CLOSED")
    failure_threshold = Column(Integer, nullable=False, default=5)
    recovery_time_seconds = Column(Integer, nullable=False, default=60)
    failure_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    last_failure_at = Column(DateTime(timezone=True), nullable=True)
    last_state_change_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    metadata_json = Column(Text, nullable=False, default="{}")


class ResiliencePolicyModel(Base):
    __tablename__ = "resilience_policies"

    id = Column(String(64), primary_key=True)
    target_name = Column(String(255), nullable=False, unique=True, index=True)
    retry_policy_json = Column(Text, nullable=False, default="{}")
    timeout_policy_json = Column(Text, nullable=False, default="{}")
    circuit_breaker_enabled = Column(Boolean, nullable=False, default=True)
    fallback_enabled = Column(Boolean, nullable=False, default=True)
    degradation_behavior = Column(String(64), nullable=False, default="NORMAL")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class SecurityIncidentModel(Base):
    __tablename__ = "security_incidents"

    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    severity = Column(String(64), nullable=False, default="HIGH", index=True)
    status = Column(String(64), nullable=False, default="DETECTED", index=True)
    affected_components_json = Column(Text, nullable=False, default="[]")
    governance_approval_id = Column(String(64), nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class SecuritySignalModel(Base):
    __tablename__ = "security_signals"

    id = Column(String(64), primary_key=True)
    source = Column(String(255), nullable=False)
    signal_type = Column(String(64), nullable=False, default="PROMPT_INJECTION_ATTEMPT", index=True)
    severity = Column(String(64), nullable=False, default="HIGH")
    raw_content = Column(Text, nullable=False, default="")
    sanitized_content = Column(Text, nullable=False, default="")
    is_blocked = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class AuditTrailLogModel(Base):
    __tablename__ = "audit_trail_logs"

    id = Column(String(64), primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    actor_id = Column(String(64), nullable=False, index=True)
    actor_type = Column(String(64), nullable=False, default="AGENT")
    enterprise_id = Column(String(64), nullable=True)
    company_id = Column(String(64), nullable=True)
    action = Column(String(128), nullable=False, index=True)
    resource = Column(String(255), nullable=False)
    previous_state = Column(Text, nullable=True)
    new_state = Column(Text, nullable=True)
    checksum = Column(String(64), nullable=False)
    correlation_id = Column(String(64), nullable=False)


class DependencyHealthSnapshotModel(Base):
    __tablename__ = "dependency_health_snapshots"

    id = Column(String(64), primary_key=True)
    dependency_name = Column(String(255), nullable=False, index=True)
    is_available = Column(Boolean, nullable=False, default=True)
    latency_ms = Column(Float, nullable=False, default=0.0)
    error_rate_pct = Column(Float, nullable=False, default=0.0)
    circuit_state = Column(String(64), nullable=False, default="CLOSED")
    last_checked_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class ProductionReadinessItemModel(Base):
    __tablename__ = "production_readiness_items"

    id = Column(String(64), primary_key=True)
    domain = Column(String(64), nullable=False, index=True)
    requirement = Column(String(255), nullable=False)
    status = Column(String(64), nullable=False, default="PASSED")
    evidence_reference = Column(Text, nullable=False, default="")
    tested_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
