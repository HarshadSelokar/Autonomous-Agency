"""
SQLAlchemy ORM model for append-only audit trail (Phase 40).
"""

from datetime import UTC, datetime
from sqlalchemy import Column, String, DateTime, JSON
from src.infrastructure.database import Base


class AuditRecordV2Model(Base):
    __tablename__ = "audit_records_v2"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    resource = Column(String(256), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    prev_hash = Column(String(64), nullable=False, default="")
    hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)
