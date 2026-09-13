"""
Unit tests for Meeting domain entity and lifecycle state transitions.
"""

from datetime import UTC, datetime, timedelta
import pytest

from src.domain.meeting import (
    Meeting,
    MeetingPurpose,
    MeetingStateError,
    MeetingStatus,
    MeetingValidationError,
)


def test_meeting_creation_and_validation() -> None:
    now = datetime.now(UTC)
    meeting = Meeting(
        id="m-100",
        title="Architecture Sync",
        purpose=MeetingPurpose.REVIEW,
        organizer_employee_id="emp-1",
        scheduled_start=now,
        scheduled_end=now + timedelta(hours=1),
    )
    assert meeting.id == "m-100"
    assert meeting.status == MeetingStatus.PROPOSED
    assert meeting.purpose == MeetingPurpose.REVIEW


def test_meeting_validation_invalid_time() -> None:
    now = datetime.now(UTC)
    with pytest.raises(MeetingValidationError, match="scheduled_end must be strictly after"):
        Meeting(
            id="m-101",
            title="Invalid Time Meeting",
            purpose=MeetingPurpose.PLANNING,
            organizer_employee_id="emp-1",
            scheduled_start=now,
            scheduled_end=now - timedelta(minutes=10),
        )


def test_meeting_empty_fields_validation() -> None:
    with pytest.raises(MeetingValidationError, match="Meeting ID cannot be empty"):
        Meeting(id="", title="Test", purpose=MeetingPurpose.STATUS, organizer_employee_id="emp-1")

    with pytest.raises(MeetingValidationError, match="Meeting title cannot be empty"):
        Meeting(id="m-1", title="   ", purpose=MeetingPurpose.STATUS, organizer_employee_id="emp-1")

    with pytest.raises(MeetingValidationError, match="organizer_employee_id cannot be empty"):
        Meeting(id="m-1", title="Test", purpose=MeetingPurpose.STATUS, organizer_employee_id="")


def test_meeting_lifecycle_transitions() -> None:
    meeting = Meeting(
        id="m-200",
        title="Sprint Planning",
        purpose=MeetingPurpose.PLANNING,
        organizer_employee_id="emp-mgr",
    )
    assert meeting.status == MeetingStatus.PROPOSED

    # PROPOSED -> SCHEDULED
    meeting.transition_to(MeetingStatus.SCHEDULED)
    assert meeting.status == MeetingStatus.SCHEDULED

    # SCHEDULED -> STARTING
    meeting.transition_to(MeetingStatus.STARTING)
    assert meeting.status == MeetingStatus.STARTING
    assert meeting.actual_start is not None

    # STARTING -> IN_PROGRESS
    meeting.transition_to(MeetingStatus.IN_PROGRESS)
    assert meeting.status == MeetingStatus.IN_PROGRESS

    # IN_PROGRESS -> ENDED
    meeting.transition_to(MeetingStatus.ENDED)
    assert meeting.status == MeetingStatus.ENDED
    assert meeting.actual_end is not None


def test_invalid_lifecycle_transition() -> None:
    meeting = Meeting(
        id="m-300",
        title="Direct End Test",
        purpose=MeetingPurpose.DECISION,
        organizer_employee_id="emp-1",
    )
    # Cannot jump from PROPOSED to ENDED directly
    with pytest.raises(MeetingStateError, match="Invalid meeting transition"):
        meeting.transition_to(MeetingStatus.ENDED)


def test_cancellation_from_allowed_states() -> None:
    meeting = Meeting(
        id="m-400",
        title="To be cancelled",
        purpose=MeetingPurpose.INCIDENT,
        organizer_employee_id="emp-1",
    )
    meeting.transition_to(MeetingStatus.SCHEDULED)
    meeting.transition_to(MeetingStatus.CANCELLED)
    assert meeting.status == MeetingStatus.CANCELLED

    # Cannot transition from CANCELLED to anything
    with pytest.raises(MeetingStateError):
        meeting.transition_to(MeetingStatus.SCHEDULED)
