"""
Unit tests for AgentMeetingAssistant and Decision proposals.
Verifies that Agent proposals remain PROPOSED and cannot bypass approval authority.
"""

import pytest

from src.application.agent_meeting_assistant import AgentMeetingAssistant
from src.domain.decision import DecisionProvenance, DecisionStatus
from src.domain.meeting import Meeting, MeetingPurpose, ParticipantRole
from tests.unit.test_decision_integration import MemoryDecisionRepository
from tests.unit.test_meeting_scheduling import MemoryMeetingRepository


@pytest.mark.asyncio
async def test_agent_decision_proposal_remains_proposed() -> None:
    meeting_repo = MemoryMeetingRepository()
    decision_repo = MemoryDecisionRepository()

    meeting = Meeting(
        id="m-ai-1",
        title="Architecture Discussion",
        purpose=MeetingPurpose.DECISION,
        organizer_employee_id="emp-mgr",
    )
    meeting.add_participant("emp-dev", role=ParticipantRole.REQUIRED, agent_id="agent-dev")
    await meeting_repo.save(meeting)

    assistant = AgentMeetingAssistant(meeting_repo=meeting_repo, decision_repo=decision_repo)

    proposal = await assistant.propose_decision_from_meeting(
        meeting_id="m-ai-1",
        title="Use Redis for Cache",
        question="Which cache provider to select?",
        recommended_option="Redis",
        rationale="Low latency and key expiration support.",
        agent_id="agent-dev",
        proposer_employee_id="emp-dev",
        alternatives=["Memcached"],
    )

    # Invariant checks: Status MUST be PROPOSED, Provenance MUST be AGENT_ASSISTED
    assert proposal.status == DecisionStatus.PROPOSED
    assert proposal.provenance == DecisionProvenance.AGENT_ASSISTED
    assert proposal.chosen_option == "Redis"
    assert "AGENT PROPOSAL" in proposal.rationale

    # Verify stored proposal is NOT approved automatically
    stored = await decision_repo.get_by_id(proposal.id)
    assert stored is not None
    assert stored.status == DecisionStatus.PROPOSED


@pytest.mark.asyncio
async def test_agent_propose_action_item() -> None:
    meeting_repo = MemoryMeetingRepository()
    decision_repo = MemoryDecisionRepository()

    meeting = Meeting(
        id="m-ai-2",
        title="Sprint Review",
        purpose=MeetingPurpose.REVIEW,
        organizer_employee_id="emp-mgr",
    )
    await meeting_repo.save(meeting)

    assistant = AgentMeetingAssistant(meeting_repo=meeting_repo, decision_repo=decision_repo)

    item = await assistant.propose_action_item(
        meeting_id="m-ai-2",
        title="Update Swagger Specs",
        agent_id="agent-dev",
        owner_employee_id="emp-dev",
    )

    assert "[AI Proposed] Update Swagger Specs" in item.title
    fetched_m = await meeting_repo.get_by_id("m-ai-2")
    assert fetched_m is not None
    assert len(fetched_m.agenda_items) == 1
