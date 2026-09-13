"""
AgentMeetingAssistant Application Layer for Phase 6.
Provides controlled agent capabilities for meeting assistance, briefings, summaries,
and decision proposals while strictly enforcing the rule:
Agent proposal ≠ Authoritative decision. LLM/Agents CANNOT approve decisions.
"""

from typing import Any

from src.domain.decision import Decision, DecisionProvenance, DecisionStatus, DecisionType
from src.domain.exceptions import ObjectiveValidationError
from src.domain.meeting import AgendaItem, Meeting
from src.domain.repository import DecisionRepositoryInterface, MeetingRepositoryInterface


class AgentMeetingAssistant:
    def __init__(
        self,
        meeting_repo: MeetingRepositoryInterface,
        decision_repo: DecisionRepositoryInterface,
        context_builder: Any = None,
    ) -> None:
        self.meeting_repo = meeting_repo
        self.decision_repo = decision_repo
        self.context_builder = context_builder

    async def prepare_meeting_briefing(
        self,
        meeting_id: str,
        requesting_agent_id: str,
        requesting_employee_id: str,
    ) -> dict[str, Any]:
        """Prepare briefing context for an upcoming or in-progress meeting."""
        meeting = await self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise ObjectiveValidationError(f"Meeting {meeting_id} not found.")

        if self.context_builder:
            return await self.context_builder.build_context(
                meeting_id=meeting_id, requesting_employee_id=requesting_employee_id
            )

        return {
            "meeting_id": meeting.id,
            "title": meeting.title,
            "purpose": meeting.purpose.value,
            "status": meeting.status.value,
            "agenda_count": len(meeting.agenda_items),
        }

    async def propose_decision_from_meeting(
        self,
        meeting_id: str,
        title: str,
        question: str,
        recommended_option: str,
        rationale: str,
        agent_id: str,
        proposer_employee_id: str,
        alternatives: list[str] | None = None,
        evidence: list[str] | None = None,
    ) -> Decision:
        """
        Create an Agent-assisted Decision proposal.
        INVARIANT: Proposal status MUST be PROPOSED, and provenance AGENT_ASSISTED.
        An Agent can NEVER set status to APPROVED.
        """
        meeting = await self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise ObjectiveValidationError(f"Meeting {meeting_id} not found.")

        proposal = Decision(
            id=f"dec-prop-{meeting_id[:6]}-{title.lower().replace(' ', '-')[:12]}",
            title=title,
            question=question,
            decision_maker_employee_id=proposer_employee_id,
            status=DecisionStatus.PROPOSED,
            chosen_option=recommended_option,
            rationale=f"[AGENT PROPOSAL via {agent_id}] {rationale}",
            alternatives=alternatives or [],
            evidence=evidence or [f"Meeting {meeting_id} Discussion"],
            meeting_id=meeting.id,
            objective_id=meeting.objective_id,
            task_id=meeting.task_id,
            provenance=DecisionProvenance.AGENT_ASSISTED,
            metadata={"agent_id": agent_id, "proposer_employee_id": proposer_employee_id},
        )

        saved = await self.decision_repo.save(proposal)
        return saved

    async def propose_action_item(
        self,
        meeting_id: str,
        title: str,
        agent_id: str,
        owner_employee_id: str | None = None,
        task_id: str | None = None,
    ) -> AgendaItem:
        """Propose an agenda action item during or after a meeting."""
        meeting = await self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            raise ObjectiveValidationError(f"Meeting {meeting_id} not found.")

        item = meeting.add_agenda_item(
            item_id=f"ag-prop-{len(meeting.agenda_items)+1}",
            title=f"[AI Proposed] {title}",
            description=f"Proposed by Agent {agent_id}",
            owner_employee_id=owner_employee_id,
            task_id=task_id,
        )
        await self.meeting_repo.save(meeting)
        return item
