"""
Unit tests for Meeting domain entity, lifecycle, participants, and attendance tracking.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.domain.meeting import (
    AttendanceStatus,
    Meeting,
    MeetingPurpose,
    MeetingStatus,
    MeetingValidationError,
    ParticipantRole,
)


def test_meeting_creation_and_organizer_auto_participant() -> None:
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
    assert "emp-1" in meeting.participants
    assert meeting.participants["emp-1"].role == ParticipantRole.ORGANIZER
    assert meeting.attendance_records["emp-1"].status == AttendanceStatus.INVITED


def test_meeting_participant_management() -> None:
    meeting = Meeting(
        id="m-101",
        title="Design Review",
        purpose=MeetingPurpose.PLANNING,
        organizer_employee_id="emp-mgr",
    )

    # Add required participant
    meeting.add_participant("emp-dev1", role=ParticipantRole.REQUIRED)
    assert "emp-dev1" in meeting.participants
    assert meeting.participants["emp-dev1"].role == ParticipantRole.REQUIRED
    assert meeting.attendance_records["emp-dev1"].status == AttendanceStatus.INVITED

    # Add presenter with agent binding
    meeting.add_participant("emp-dev2", role=ParticipantRole.PRESENTER, agent_id="agent-42")
    assert meeting.participants["emp-dev2"].agent_id == "agent-42"

    # Duplicate participant with same role fails
    with pytest.raises(MeetingValidationError, match="already exists in meeting"):
        meeting.add_participant("emp-dev1", role=ParticipantRole.REQUIRED)

    # Remove participant
    meeting.remove_participant("emp-dev1")
    assert "emp-dev1" not in meeting.participants
    assert "emp-dev1" not in meeting.attendance_records

    # Cannot remove organizer
    with pytest.raises(MeetingValidationError, match="Cannot remove the organizer"):
        meeting.remove_participant("emp-mgr")


def test_meeting_attendance_tracking() -> None:
    meeting = Meeting(
        id="m-102",
        title="Status Standup",
        purpose=MeetingPurpose.STATUS,
        organizer_employee_id="emp-mgr",
    )
    meeting.add_participant("emp-1", role=ParticipantRole.REQUIRED)

    # Record attendance
    meeting.record_attendance("emp-1", AttendanceStatus.ACCEPTED)
    assert meeting.attendance_records["emp-1"].status == AttendanceStatus.ACCEPTED

    meeting.record_attendance("emp-1", AttendanceStatus.ATTENDED, notes="Present on time")
    assert meeting.attendance_records["emp-1"].status == AttendanceStatus.ATTENDED
    assert meeting.attendance_records["emp-1"].notes == "Present on time"

    # Record attendance for non-participant fails
    with pytest.raises(MeetingValidationError, match="not an invited participant"):
        meeting.record_attendance("emp-outsider", AttendanceStatus.ATTENDED)


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
