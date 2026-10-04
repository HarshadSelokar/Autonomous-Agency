"""
SQLAlchemy models for Phase 39 Resilience V2.
"""

from datetime import UTC, datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON
from src.infrastructure.database import Base


class ResilienceV2PolicyModel(Base):
    __tablename__ = "resilience_v2_policies"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, unique=True, index=True)
    max_retries = Column(Integer, nullable=False, default=3)
    circuit_breaker_threshold = Column(Integer, nullable=False, default=5)
    auto_self_healing = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))


class SelfHealingLogModel(Base):
    __tablename__ = "self_healing_logs"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    fault_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False, default="MODERATE")
    action_taken = Column(String(50), nullable=False)
    success = Column(Boolean, nullable=False, default=True)
    details = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
