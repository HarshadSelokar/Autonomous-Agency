"""
Meeting Domain Entity, Lifecycle, Participants, and Attendance for Phase 6.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from src.domain.exceptions import ObjectiveValidationError


class MeetingPurpose(str, Enum):
    PLANNING = "PLANNING"
    STATUS = "STATUS"
    REVIEW = "REVIEW"
    DECISION = "DECISION"
    BLOCKER_RESOLUTION = "BLOCKER_RESOLUTION"
    INCIDENT = "INCIDENT"
    COORDINATION = "COORDINATION"


class MeetingStatus(str, Enum):
    PROPOSED = "PROPOSED"
    SCHEDULED = "SCHEDULED"
    STARTING = "STARTING"
    IN_PROGRESS = "IN_PROGRESS"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"


class ParticipantRole(str, Enum):
    ORGANIZER = "ORGANIZER"
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    OBSERVER = "OBSERVER"
    PRESENTER = "PRESENTER"


class AttendanceStatus(str, Enum):
    INVITED = "INVITED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    ATTENDED = "ATTENDED"
    ABSENT = "ABSENT"


class MeetingValidationError(ObjectiveValidationError):
    """Raised when meeting domain constraints or state transitions are violated."""

    pass


class MeetingStateError(MeetingValidationError):
    """Raised when an invalid meeting lifecycle transition is attempted."""

    pass


VALID_MEETING_TRANSITIONS: dict[MeetingStatus, set[MeetingStatus]] = {
    MeetingStatus.PROPOSED: {MeetingStatus.SCHEDULED, MeetingStatus.CANCELLED},
    MeetingStatus.SCHEDULED: {MeetingStatus.STARTING, MeetingStatus.CANCELLED},
    MeetingStatus.STARTING: {MeetingStatus.IN_PROGRESS, MeetingStatus.CANCELLED},
    MeetingStatus.IN_PROGRESS: {MeetingStatus.ENDED, MeetingStatus.CANCELLED},
    MeetingStatus.ENDED: set(),
    MeetingStatus.CANCELLED: set(),
}


@dataclass
class MeetingParticipant:
    meeting_id: str
    employee_id: str
    role: ParticipantRole = ParticipantRole.REQUIRED
    agent_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.meeting_id or not self.meeting_id.strip():
            raise MeetingValidationError("Participant meeting_id cannot be empty.")
        if not self.employee_id or not self.employee_id.strip():
            raise MeetingValidationError("Participant employee_id cannot be empty.")


@dataclass
class MeetingAttendance:
    meeting_id: str
    employee_id: str
    status: AttendanceStatus = AttendanceStatus.INVITED
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.meeting_id or not self.meeting_id.strip():
            raise MeetingValidationError("Attendance meeting_id cannot be empty.")
        if not self.employee_id or not self.employee_id.strip():
            raise MeetingValidationError("Attendance employee_id cannot be empty.")


@dataclass
class Meeting:
    id: str
    title: str
    purpose: MeetingPurpose
    organizer_employee_id: str
    status: MeetingStatus = MeetingStatus.PROPOSED
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    conversation_id: str | None = None
    objective_id: str | None = None
    plan_id: str | None = None
    task_id: str | None = None
    project_id: str | None = None
    participants: dict[str, MeetingParticipant] = field(default_factory=dict)
    attendance_records: dict[str, MeetingAttendance] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validate()
        # Automatically register organizer as an ORGANIZER participant if not present
        if self.organizer_employee_id and self.organizer_employee_id not in self.participants:
            self.add_participant(
                employee_id=self.organizer_employee_id, role=ParticipantRole.ORGANIZER
            )

    def validate(self) -> None:
        if not self.id or not self.id.strip():
            raise MeetingValidationError("Meeting ID cannot be empty.")
        if not self.title or not self.title.strip():
            raise MeetingValidationError("Meeting title cannot be empty.")
        if not self.organizer_employee_id or not self.organizer_employee_id.strip():
            raise MeetingValidationError("Meeting organizer_employee_id cannot be empty.")
        if self.scheduled_start and self.scheduled_end:
            if self.scheduled_end <= self.scheduled_start:
                raise MeetingValidationError("scheduled_end must be strictly after scheduled_start.")

    def add_participant(
        self,
        employee_id: str,
        role: ParticipantRole = ParticipantRole.REQUIRED,
        agent_id: str | None = None,
    ) -> MeetingParticipant:
        """Add a participant to the meeting. Prevents duplicates and initializes attendance."""
        if not employee_id or not employee_id.strip():
            raise MeetingValidationError("Participant employee_id cannot be empty.")
        if employee_id in self.participants and self.participants[employee_id].role == role:
            raise MeetingValidationError(
                f"Participant employee {employee_id} already exists in meeting with role {role.value}."
            )

        participant = MeetingParticipant(
            meeting_id=self.id,
            employee_id=employee_id,
            role=role,
            agent_id=agent_id,
        )
        self.participants[employee_id] = participant

        # Initialize attendance as INVITED if not present
        if employee_id not in self.attendance_records:
            self.attendance_records[employee_id] = MeetingAttendance(
                meeting_id=self.id,
                employee_id=employee_id,
                status=AttendanceStatus.INVITED,
            )
        return participant

    def remove_participant(self, employee_id: str) -> None:
        """Remove a participant from the meeting (cannot remove the organizer)."""
        if employee_id == self.organizer_employee_id:
            raise MeetingValidationError("Cannot remove the organizer from the meeting.")
        if employee_id not in self.participants:
            raise MeetingValidationError(
                f"Participant employee {employee_id} is not in meeting {self.id}."
            )
        del self.participants[employee_id]
        self.attendance_records.pop(employee_id, None)

    def record_attendance(
        self, employee_id: str, status: AttendanceStatus, notes: str | None = None
    ) -> MeetingAttendance:
        """Record attendance status for a participant."""
        if employee_id not in self.participants:
            raise MeetingValidationError(
                f"Employee {employee_id} is not an invited participant of meeting {self.id}."
            )
        record = MeetingAttendance(
            meeting_id=self.id,
            employee_id=employee_id,
            status=status,
            notes=notes,
        )
        self.attendance_records[employee_id] = record
        return record

    def transition_to(self, target_status: MeetingStatus) -> None:
        """Execute a deterministic state transition."""
        allowed = VALID_MEETING_TRANSITIONS.get(self.status, set())
        if target_status not in allowed:
            raise MeetingStateError(
                f"Invalid meeting transition from {self.status.value} to {target_status.value}."
            )
        now = datetime.now(UTC)
        if target_status in {MeetingStatus.STARTING, MeetingStatus.IN_PROGRESS}:
            if self.actual_start is None:
                self.actual_start = now
        elif target_status == MeetingStatus.ENDED:
            self.actual_end = now
        self.status = target_status
        self.updated_at = now
