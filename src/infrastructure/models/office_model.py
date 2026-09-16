"""
SQLAlchemy ORM Models for Phase 13 Pixel Office Projections & Activity Feed.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text

from src.infrastructure.database import Base


class OfficeWorkstationModel(Base):
    __tablename__ = "office_workstations"

    employee_id = Column(String(64), primary_key=True, index=True)
    employee_name = Column(String(128), nullable=False)
    employee_title = Column(String(128), nullable=False)
    role = Column(String(64), nullable=False)
    department_id = Column(String(64), nullable=True, index=True)
    manager_id = Column(String(64), nullable=True, index=True)
    desk_id = Column(String(64), nullable=False)
    area_type = Column(String(64), nullable=False)
    visual_state = Column(String(64), nullable=False, index=True)
    current_task_id = Column(String(64), nullable=True)
    current_task_title = Column(String(256), nullable=True)
    current_project_id = Column(String(64), nullable=True)
    current_project_name = Column(String(128), nullable=True)
    current_activity_summary = Column(Text, nullable=False, default="Idle")
    active_agent_id = Column(String(64), nullable=True)
    active_tool_name = Column(String(128), nullable=True)
    active_model_id = Column(String(128), nullable=True)
    is_manager = Column(Boolean, default=False)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))


class OfficeActivityModel(Base):
    __tablename__ = "office_activity_feed"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)


class HumanAttentionModel(Base):
    __tablename__ = "human_attention_queue"

    id = Column(String(64), primary_key=True, index=True)
    attention_type = Column(String(64), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    entity_id = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False, default="HIGH")
    action_url = Column(String(256), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
