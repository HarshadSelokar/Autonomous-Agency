"""
SQLAlchemy ORM Models for Meeting, Participant, Attendance, and Agenda persistence.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.meeting import (
    AgendaItem,
    AgendaItemStatus,
    AttendanceStatus,
    Meeting,
    MeetingAttendance,
    MeetingParticipant,
    MeetingPurpose,
    MeetingStatus,
    ParticipantRole,
)
from src.infrastructure.database import Base


class MeetingModel(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    organizer_employee_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
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
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    participants: Mapped[list["MeetingParticipantModel"]] = relationship(
        "MeetingParticipantModel", back_populates="meeting", cascade="all, delete-orphan", lazy="joined"
    )
    attendance_records: Mapped[list["MeetingAttendanceModel"]] = relationship(
        "MeetingAttendanceModel", back_populates="meeting", cascade="all, delete-orphan", lazy="joined"
    )
    agenda_items: Mapped[list["MeetingAgendaItemModel"]] = relationship(
        "MeetingAgendaItemModel", back_populates="meeting", cascade="all, delete-orphan", lazy="joined"
    )


class MeetingParticipantModel(Base):
    __tablename__ = "meeting_participants"

    meeting_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    )
    employee_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    meeting: Mapped["MeetingModel"] = relationship("MeetingModel", back_populates="participants")


class MeetingAttendanceModel(Base):
    __tablename__ = "meeting_attendance"

    meeting_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True
    )
    employee_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="RESTRICT"), primary_key=True, index=True
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    meeting: Mapped["MeetingModel"] = relationship("MeetingModel", back_populates="attendance_records")


class MeetingAgendaItemModel(Base):
    __tablename__ = "meeting_agenda_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    owner_employee_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    task_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    objective_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("objectives.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    meeting: Mapped["MeetingModel"] = relationship("MeetingModel", back_populates="agenda_items")


def meeting_model_to_domain(model: MeetingModel) -> Meeting:
    participants = {
        p.employee_id: MeetingParticipant(
            meeting_id=p.meeting_id,
            employee_id=p.employee_id,
            role=ParticipantRole(p.role),
            agent_id=p.agent_id,
            created_at=p.created_at,
        )
        for p in model.participants
    }

    attendance_records = {
        a.employee_id: MeetingAttendance(
            meeting_id=a.meeting_id,
            employee_id=a.employee_id,
            status=AttendanceStatus(a.status),
            recorded_at=a.recorded_at,
            notes=a.notes,
        )
        for a in model.attendance_records
    }

    sorted_agenda = sorted(model.agenda_items, key=lambda item: item.order)
    agenda_items = [
        AgendaItem(
            id=ag.id,
            meeting_id=ag.meeting_id,
            order=ag.order,
            title=ag.title,
            description=ag.description,
            owner_employee_id=ag.owner_employee_id,
            duration_minutes=ag.duration_minutes,
            task_id=ag.task_id,
            objective_id=ag.objective_id,
            status=AgendaItemStatus(ag.status),
            created_at=ag.created_at,
        )
        for ag in sorted_agenda
    ]

    return Meeting(
        id=model.id,
        title=model.title,
        purpose=MeetingPurpose(model.purpose),
        organizer_employee_id=model.organizer_employee_id,
        status=MeetingStatus(model.status),
        scheduled_start=model.scheduled_start,
        scheduled_end=model.scheduled_end,
        actual_start=model.actual_start,
        actual_end=model.actual_end,
        conversation_id=model.conversation_id,
        objective_id=model.objective_id,
        plan_id=model.plan_id,
        task_id=model.task_id,
        project_id=model.project_id,
        participants=participants,
        attendance_records=attendance_records,
        agenda_items=agenda_items,
        metadata=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def meeting_domain_to_model(domain: Meeting) -> MeetingModel:
    participant_models = [
        MeetingParticipantModel(
            meeting_id=domain.id,
            employee_id=p.employee_id,
            role=p.role.value,
            agent_id=p.agent_id,
            created_at=p.created_at,
        )
        for p in domain.participants.values()
    ]

    attendance_models = [
        MeetingAttendanceModel(
            meeting_id=domain.id,
            employee_id=a.employee_id,
            status=a.status.value,
            recorded_at=a.recorded_at,
            notes=a.notes,
        )
        for a in domain.attendance_records.values()
    ]

    agenda_models = [
        MeetingAgendaItemModel(
            id=ag.id,
            meeting_id=domain.id,
            order=ag.order,
            title=ag.title,
            description=ag.description,
            owner_employee_id=ag.owner_employee_id,
            duration_minutes=ag.duration_minutes,
            task_id=ag.task_id,
            objective_id=ag.objective_id,
            status=ag.status.value,
            created_at=ag.created_at,
        )
        for ag in domain.agenda_items
    ]

    return MeetingModel(
        id=domain.id,
        title=domain.title,
        purpose=domain.purpose.value,
        status=domain.status.value,
        organizer_employee_id=domain.organizer_employee_id,
        scheduled_start=domain.scheduled_start,
        scheduled_end=domain.scheduled_end,
        actual_start=domain.actual_start,
        actual_end=domain.actual_end,
        conversation_id=domain.conversation_id,
        objective_id=domain.objective_id,
        plan_id=domain.plan_id,
        task_id=domain.task_id,
        project_id=domain.project_id,
        metadata_json=domain.metadata,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
        participants=participant_models,
        attendance_records=attendance_models,
        agenda_items=agenda_models,
    )
