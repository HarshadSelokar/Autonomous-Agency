"""
MeetingSchedulingService Application Layer for Phase 6.
Handles meeting scheduling, participant availability, time range validation, and conflict detection.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from src.domain.events import DomainEvent
from src.domain.exceptions import EmployeeNotFoundError
from src.domain.meeting import (
    Meeting,
    MeetingPurpose,
    MeetingSchedulingConflictError,
    MeetingStatus,
    MeetingValidationError,
    ParticipantRole,
)
from src.domain.repository import EmployeeRepositoryInterface, MeetingRepositoryInterface

if TYPE_CHECKING:
    from src.application.event_dispatcher import EventDispatcher


class MeetingScheduledEvent(DomainEvent):
    meeting_id: str
    organizer_employee_id: str
    participant_employee_ids: list[str]
    scheduled_start: str
    scheduled_end: str


class MeetingSchedulingService:
    def __init__(
        self,
        meeting_repo: MeetingRepositoryInterface,
        employee_repo: EmployeeRepositoryInterface,
        event_dispatcher: "EventDispatcher | None" = None,
    ) -> None:
        self.meeting_repo = meeting_repo
        self.employee_repo = employee_repo
        self.event_dispatcher = event_dispatcher

    async def create_meeting(
        self,
        meeting_id: str,
        title: str,
        purpose: MeetingPurpose,
        organizer_employee_id: str,
        participant_ids: list[str] | None = None,
        objective_id: str | None = None,
        plan_id: str | None = None,
        task_id: str | None = None,
    ) -> Meeting:
        """Create a new proposed meeting after validating organizer and participants."""
        organizer = await self.employee_repo.get_by_id(organizer_employee_id)
        if not organizer or organizer.status.value != "ACTIVE":
            raise EmployeeNotFoundError(
                f"Organizer employee {organizer_employee_id} not found or inactive."
            )

        meeting = Meeting(
            id=meeting_id,
            title=title,
            purpose=purpose,
            organizer_employee_id=organizer_employee_id,
            objective_id=objective_id,
            plan_id=plan_id,
            task_id=task_id,
        )

        if participant_ids:
            for pid in participant_ids:
                if pid == organizer_employee_id:
                    continue
                emp = await self.employee_repo.get_by_id(pid)
                if not emp or emp.status.value != "ACTIVE":
                    raise EmployeeNotFoundError(f"Participant employee {pid} not found or inactive.")
                meeting.add_participant(employee_id=pid, role=ParticipantRole.REQUIRED)

        return await self.meeting_repo.save(meeting)

    async def schedule_meeting(
        self,
        meeting_id: str,
        scheduled_start: datetime,
        scheduled_end: datetime,
    ) -> Meeting:
        """Schedule a meeting after validating time ranges and checking participant conflicts."""
        meeting = await self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise MeetingValidationError(f"Meeting {meeting_id} not found.")

        # Time range validation
        if scheduled_end <= scheduled_start:
            raise MeetingValidationError("scheduled_end must be strictly after scheduled_start.")

        # Ensure timezone awareness
        if scheduled_start.tzinfo is None:
            scheduled_start = scheduled_start.replace(tzinfo=UTC)
        if scheduled_end.tzinfo is None:
            scheduled_end = scheduled_end.replace(tzinfo=UTC)

        meeting.scheduled_start = scheduled_start
        meeting.scheduled_end = scheduled_end

        # Check scheduling conflicts across all active scheduled meetings
        all_meetings = await self.meeting_repo.list_all()
        active_statuses = {MeetingStatus.SCHEDULED, MeetingStatus.STARTING, MeetingStatus.IN_PROGRESS}

        meeting_participant_ids = set(meeting.participants.keys())

        for existing in all_meetings:
            if existing.id == meeting.id:
                continue
            if existing.status not in active_statuses:
                continue
            if not existing.scheduled_start or not existing.scheduled_end:
                continue

            # Check time overlap
            if (existing.scheduled_start < scheduled_end) and (existing.scheduled_end > scheduled_start):
                existing_participant_ids = set(existing.participants.keys())
                overlapping_employees = meeting_participant_ids.intersection(existing_participant_ids)

                if overlapping_employees:
                    emp_id = list(overlapping_employees)[0]
                    raise MeetingSchedulingConflictError(
                        f"Participant {emp_id} has a scheduling conflict with existing meeting '{existing.title}' ({existing.id})."
                    )

        # Transition meeting state
        meeting.transition_to(MeetingStatus.SCHEDULED)
        saved = await self.meeting_repo.save(meeting)

        # Dispatch domain event if dispatcher provided
        if self.event_dispatcher:
            event = MeetingScheduledEvent(
                meeting_id=saved.id,
                organizer_employee_id=saved.organizer_employee_id,
                participant_employee_ids=list(saved.participants.keys()),
                scheduled_start=scheduled_start.isoformat(),
                scheduled_end=scheduled_end.isoformat(),
            )
            await self.event_dispatcher.dispatch(event)

        return saved
