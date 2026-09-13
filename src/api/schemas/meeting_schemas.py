"""
Pydantic API Schemas for Meetings & Agenda Management.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class CreateMeetingRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    purpose: str = Field(..., description="PLANNING, STATUS, REVIEW, DECISION, BLOCKER_RESOLUTION, INCIDENT, COORDINATION")
    organizer_employee_id: str = Field(..., min_length=1)
    participant_ids: list[str] = Field(default_factory=list)
    objective_id: str | None = None
    plan_id: str | None = None
    task_id: str | None = None
    project_id: str | None = None


class ScheduleMeetingRequest(BaseModel):
    scheduled_start: datetime
    scheduled_end: datetime


class AddParticipantRequest(BaseModel):
    employee_id: str
    role: str = "REQUIRED"
    agent_id: str | None = None


class AddAgendaItemRequest(BaseModel):
    title: str
    description: str | None = None
    owner_employee_id: str | None = None
    duration_minutes: int | None = None
    task_id: str | None = None
    objective_id: str | None = None


class RecordAttendanceRequest(BaseModel):
    employee_id: str
    status: str = Field(..., description="INVITED, ACCEPTED, DECLINED, ATTENDED, ABSENT")
    notes: str | None = None


class MeetingResponse(BaseModel):
    id: str
    title: str
    purpose: str
    status: str
    organizer_employee_id: str
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    conversation_id: str | None = None
    objective_id: str | None = None
    plan_id: str | None = None
    task_id: str | None = None
    participant_count: int
    agenda_item_count: int
    created_at: datetime
