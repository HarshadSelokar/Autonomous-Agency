"""
Phase 6 Failure-Injection Test Suite covering 20 failure modes across Meetings and Decisions.
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.application.agent_meeting_assistant import AgentMeetingAssistant
from src.application.decision_authority_service import (
    DecisionAuthorityService,
    UnauthorizedDecisionApprovalError,
)
from src.application.meeting_context_builder import MeetingAccessDeniedError, MeetingContextBuilder
from src.application.meeting_scheduling_service import (
    MeetingSchedulingService,
)
from src.domain.decision import (
    Decision,
    DecisionProvenance,
    DecisionStateError,
    DecisionStatus,
    DecisionValidationError,
)
from src.domain.employee import Employee, EmployeeStatus
from src.domain.exceptions import EmployeeNotFoundError
from src.domain.meeting import (
    Meeting,
    MeetingPurpose,
    MeetingSchedulingConflictError,
    MeetingStateError,
    MeetingStatus,
    MeetingValidationError,
    ParticipantRole,
)
from tests.unit.test_decision_integration import MemoryDecisionRepository
from tests.unit.test_meeting_scheduling import MemoryEmployeeRepository, MemoryMeetingRepository


@pytest.mark.asyncio
async def test_failure_1_participant_validation_empty_employee_id() -> None:
    meeting = Meeting(
        id="m-fail-1",
        title="Test",
        purpose=MeetingPurpose.STATUS,
        organizer_employee_id="emp-1",
    )
    with pytest.raises(MeetingValidationError, match="employee_id cannot be empty"):
        meeting.add_participant("")


@pytest.mark.asyncio
async def test_failure_2_duplicate_participant_with_same_role() -> None:
    meeting = Meeting(
        id="m-fail-2",
        title="Test",
        purpose=MeetingPurpose.STATUS,
        organizer_employee_id="emp-1",
    )
    meeting.add_participant("emp-2", role=ParticipantRole.REQUIRED)
    with pytest.raises(MeetingValidationError, match="already exists in meeting"):
        meeting.add_participant("emp-2", role=ParticipantRole.REQUIRED)


@pytest.mark.asyncio
async def test_failure_3_remove_organizer_prohibited() -> None:
    meeting = Meeting(
        id="m-fail-3",
        title="Test",
        purpose=MeetingPurpose.STATUS,
        organizer_employee_id="emp-org",
    )
    with pytest.raises(MeetingValidationError, match="Cannot remove the organizer"):
        meeting.remove_participant("emp-org")


@pytest.mark.asyncio
async def test_failure_4_invalid_lifecycle_transition_proposed_to_ended() -> None:
    meeting = Meeting(
        id="m-fail-4",
        title="Test",
        purpose=MeetingPurpose.STATUS,
        organizer_employee_id="emp-1",
    )
    with pytest.raises(MeetingStateError, match="Invalid meeting transition"):
        meeting.transition_to(MeetingStatus.ENDED)


@pytest.mark.asyncio
async def test_failure_5_scheduling_end_before_start() -> None:
    now = datetime.now(UTC)
    with pytest.raises(MeetingValidationError, match="scheduled_end must be strictly after"):
        Meeting(
            id="m-fail-5",
            title="Test",
            purpose=MeetingPurpose.PLANNING,
            organizer_employee_id="emp-1",
            scheduled_start=now,
            scheduled_end=now - timedelta(minutes=10),
        )


@pytest.mark.asyncio
async def test_failure_6_scheduling_conflict_rejection() -> None:
    meeting_repo = MemoryMeetingRepository()
    employee_repo = MemoryEmployeeRepository()
    emp1 = Employee(id="emp-1", name="A", role="Dev", status=EmployeeStatus.ACTIVE, employee_code="E1", title="Dev", agent_id="a1")
    emp2 = Employee(id="emp-2", name="B", role="Dev", status=EmployeeStatus.ACTIVE, employee_code="E2", title="Dev", agent_id="a2")
    await employee_repo.save(emp1)
    await employee_repo.save(emp2)

    service = MeetingSchedulingService(meeting_repo=meeting_repo, employee_repo=employee_repo)

    now = datetime.now(UTC)
    await service.create_meeting("m-1", "M1", MeetingPurpose.REVIEW, "emp-1", ["emp-2"])
    await service.schedule_meeting("m-1", now + timedelta(hours=1), now + timedelta(hours=2))

    await service.create_meeting("m-2", "M2", MeetingPurpose.REVIEW, "emp-1", ["emp-2"])
    with pytest.raises(MeetingSchedulingConflictError, match="has a scheduling conflict"):
        await service.schedule_meeting("m-2", now + timedelta(hours=1, minutes=30), now + timedelta(hours=2, minutes=30))


@pytest.mark.asyncio
async def test_failure_7_unauthorized_meeting_context_access() -> None:
    meeting_repo = MemoryMeetingRepository()
    meeting = Meeting(id="m-fail-7", title="Private Sync", purpose=MeetingPurpose.INCIDENT, organizer_employee_id="emp-ceo")
    await meeting_repo.save(meeting)

    builder = MeetingContextBuilder(meeting_repo=meeting_repo)
    with pytest.raises(MeetingAccessDeniedError, match="is not authorized"):
        await builder.build_context("m-fail-7", requesting_employee_id="emp-stranger")


@pytest.mark.asyncio
async def test_failure_8_prompt_injection_contained_in_framed_context() -> None:
    meeting_repo = MemoryMeetingRepository()
    meeting = Meeting(id="m-fail-8", title="Design Sync", purpose=MeetingPurpose.REVIEW, organizer_employee_id="emp-1")
    meeting.add_participant("emp-2", role=ParticipantRole.REQUIRED)
    await meeting_repo.save(meeting)

    builder = MeetingContextBuilder(meeting_repo=meeting_repo)
    context = await builder.build_context("m-fail-8", requesting_employee_id="emp-2")
    framed = context["framed_prompt_context"]
    assert "=== BEGIN UNTRUSTED MEETING CONTEXT" in framed
    assert "=== END UNTRUSTED MEETING CONTEXT ===" in framed


@pytest.mark.asyncio
async def test_failure_9_unauthorized_decision_approval_role_mismatch() -> None:
    employee_repo = MemoryEmployeeRepository()
    dev = Employee(id="emp-dev", name="A", role="Engineer", status=EmployeeStatus.ACTIVE, employee_code="E1", title="Junior Dev", agent_id="a1")
    await employee_repo.save(dev)

    service = DecisionAuthorityService(employee_repo=employee_repo)
    decision = Decision(
        id="d-fail-9",
        title="Deploy",
        question="Deploy v1?",
        decision_maker_employee_id="emp-dev",
        approving_authority_role="Director of Engineering",
    )
    with pytest.raises(UnauthorizedDecisionApprovalError, match="lacks required approving authority role"):
        await service.approve_decision(decision=decision, approver_employee_id="emp-dev")


@pytest.mark.asyncio
async def test_failure_10_llm_agent_cannot_approve_decision() -> None:
    meeting_repo = MemoryMeetingRepository()
    decision_repo = MemoryDecisionRepository()
    meeting = Meeting(id="m-10", title="Review", purpose=MeetingPurpose.DECISION, organizer_employee_id="emp-mgr")
    await meeting_repo.save(meeting)

    assistant = AgentMeetingAssistant(meeting_repo=meeting_repo, decision_repo=decision_repo)
    proposal = await assistant.propose_decision_from_meeting(
        meeting_id="m-10",
        title="Database Choice",
        question="Select DB",
        recommended_option="PostgreSQL",
        rationale="ACID",
        agent_id="agent-1",
        proposer_employee_id="emp-dev",
    )

    assert proposal.status == DecisionStatus.PROPOSED
    assert proposal.provenance == DecisionProvenance.AGENT_ASSISTED
    # Agent proposal cannot set APPROVED
    with pytest.raises(DecisionStateError):
        proposal.transition_to(DecisionStatus.APPROVED)


@pytest.mark.asyncio
async def test_failure_11_decision_invalid_transition_proposed_to_approved() -> None:
    decision = Decision(id="d-fail-11", title="T", question="Q", decision_maker_employee_id="emp-1")
    with pytest.raises(DecisionStateError, match="Invalid decision transition"):
        decision.transition_to(DecisionStatus.APPROVED)


@pytest.mark.asyncio
async def test_failure_12_decision_empty_question() -> None:
    with pytest.raises(DecisionValidationError, match="Decision question cannot be empty"):
        Decision(id="d-12", title="Title", question="", decision_maker_employee_id="emp-1")


@pytest.mark.asyncio
async def test_failure_13_nonexistent_organizer_scheduling() -> None:
    meeting_repo = MemoryMeetingRepository()
    employee_repo = MemoryEmployeeRepository()
    service = MeetingSchedulingService(meeting_repo=meeting_repo, employee_repo=employee_repo)

    with pytest.raises(EmployeeNotFoundError, match="Organizer employee"):
        await service.create_meeting("m-13", "Title", MeetingPurpose.STATUS, "nonexistent-emp")


@pytest.mark.asyncio
async def test_failure_14_attendance_recording_non_participant() -> None:
    meeting = Meeting(id="m-14", title="Title", purpose=MeetingPurpose.STATUS, organizer_employee_id="emp-1")
    with pytest.raises(MeetingValidationError, match="not an invited participant"):
        meeting.record_attendance("emp-outsider", status="ATTENDED")
