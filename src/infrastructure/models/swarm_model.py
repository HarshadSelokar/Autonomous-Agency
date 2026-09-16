"""
SQLAlchemy ORM Models for Phase 22 Multi-Agent Swarms.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import declarative_base, relationship

from src.infrastructure.models.company_model import Base


class SwarmModel(Base):
    __tablename__ = "swarms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False)
    parent_task_id = Column(String(36), nullable=False)
    purpose = Column(Text, nullable=False)
    manager_id = Column(String(36), nullable=False)
    objective_id = Column(String(36), nullable=True)
    project_id = Column(String(36), nullable=True)
    coordinator_member_id = Column(String(36), nullable=True)
    status = Column(String(50), nullable=False, default="CREATED")
    coordination_mode = Column(String(50), nullable=False, default="PARALLEL")
    depth = Column(Integer, nullable=False, default=1)
    governance_context = Column(JSON, nullable=True)
    concurrency_limit = Column(Integer, nullable=False, default=5)
    max_agents = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    timeout_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    members = relationship("SwarmMemberModel", back_populates="swarm", cascade="all, delete-orphan")
    budget = relationship("SwarmBudgetModel", back_populates="swarm", uselist=False, cascade="all, delete-orphan")
    results = relationship("SwarmResultModel", back_populates="swarm", cascade="all, delete-orphan")
    messages = relationship("SwarmMessageModel", back_populates="swarm", cascade="all, delete-orphan")
    conflicts = relationship("SwarmConflictModel", back_populates="swarm", cascade="all, delete-orphan")


class SwarmMemberModel(Base):
    __tablename__ = "swarm_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    swarm_id = Column(String(36), ForeignKey("swarms.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(36), nullable=False)
    agent_id = Column(String(36), nullable=False)
    role = Column(String(100), nullable=False)
    capability = Column(String(100), nullable=False)
    assigned_task_id = Column(String(36), nullable=True)
    status = Column(String(50), nullable=False, default="INVITED")
    joined_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    left_at = Column(DateTime(timezone=True), nullable=True)
    execution_stats = Column(JSON, nullable=True)

    swarm = relationship("SwarmModel", back_populates="members")


class SwarmBudgetModel(Base):
    __tablename__ = "swarm_budgets"

    swarm_id = Column(String(36), ForeignKey("swarms.id", ondelete="CASCADE"), primary_key=True)
    max_execution_time_seconds = Column(Integer, nullable=False, default=3600)
    max_model_cost = Column(Float, nullable=False, default=50.0)
    max_tool_calls = Column(Integer, nullable=False, default=200)
    max_tokens = Column(Integer, nullable=False, default=500000)
    max_retries = Column(Integer, nullable=False, default=5)
    max_swarm_depth = Column(Integer, nullable=False, default=2)
    current_execution_time_seconds = Column(Integer, nullable=False, default=0)
    current_model_cost = Column(Float, nullable=False, default=0.0)
    current_tool_calls = Column(Integer, nullable=False, default=0)
    current_tokens = Column(Integer, nullable=False, default=0)
    current_retries = Column(Integer, nullable=False, default=0)

    swarm = relationship("SwarmModel", back_populates="budget")


class SwarmResultModel(Base):
    __tablename__ = "swarm_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    swarm_id = Column(String(36), ForeignKey("swarms.id", ondelete="CASCADE"), nullable=False)
    parent_task_id = Column(String(36), nullable=False)
    member_results = Column(JSON, nullable=True)
    subtask_status = Column(JSON, nullable=True)
    artifacts = Column(JSON, nullable=True)
    evidence_ids = Column(JSON, nullable=True)
    disagreements = Column(JSON, nullable=True)
    unresolved_issues = Column(JSON, nullable=True)
    aggregated_result = Column(JSON, nullable=True)
    aggregation_strategy = Column(String(100), nullable=False, default="DETERMINISTIC_MERGE")
    verification_status = Column(String(50), nullable=False, default="PENDING")
    is_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    swarm = relationship("SwarmModel", back_populates="results")


class SwarmMessageModel(Base):
    __tablename__ = "swarm_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    swarm_id = Column(String(36), ForeignKey("swarms.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String(36), nullable=False)
    recipient_id = Column(String(36), nullable=True)
    task_id = Column(String(36), nullable=True)
    message_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=True)
    correlation_id = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    swarm = relationship("SwarmModel", back_populates="messages")


class SwarmConflictModel(Base):
    __tablename__ = "swarm_conflicts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    swarm_id = Column(String(36), ForeignKey("swarms.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String(36), nullable=False)
    agent_a_id = Column(String(36), nullable=False)
    result_a = Column(JSON, nullable=True)
    agent_b_id = Column(String(36), nullable=False)
    result_b = Column(JSON, nullable=True)
    conflict_type = Column(String(100), nullable=False)
    resolution_strategy = Column(String(100), nullable=False, default="INDEPENDENT_VERIFICATION")
    resolved_result = Column(JSON, nullable=True)
    is_resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    swarm = relationship("SwarmModel", back_populates="conflicts")
