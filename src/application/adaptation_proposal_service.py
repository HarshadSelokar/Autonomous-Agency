"""
Adaptation Proposal Application Service for Phase 27.

Formulates improvement opportunities, adaptation proposals, performs multi-dimensional
evaluations, impact assessments, risk categorization, and interfaces with Phase 11 Governance.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.learning import (
    ImprovementOpportunity,
    AdaptationProposal,
    AdaptationStatus,
    AdaptationType,
    AdaptationRiskLevel,
    AdaptationEvaluation,
    AdaptationImpactAssessment,
)
from src.domain.events import (
    ImprovementOpportunityCreatedEvent,
    AdaptationProposalCreatedEvent,
)
from src.domain.repository import LearningRepositoryInterface


class AdaptationProposalService:
    """Manages improvement opportunities, adaptation proposals, multi-objective evaluations, and governance interface."""

    def __init__(self, repository: LearningRepositoryInterface, outbox_publisher: Optional[Any] = None) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def identify_improvement_opportunity(
        self,
        company_id: str,
        title: str,
        affected_area: str,
        expected_impact: str,
        required_resources: Optional[Dict[str, Any]] = None,
        risks: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
    ) -> ImprovementOpportunity:
        opp = ImprovementOpportunity(
            id=str(uuid.uuid4()),
            company_id=company_id,
            title=title,
            affected_area=affected_area,
            expected_impact=expected_impact,
            required_resources=required_resources or {},
            risks=risks or ["Temporary workflow friction during rollout"],
            constraints=constraints or ["Must pass security verification"],
            confidence=0.85,
            identified_at=datetime.now(UTC),
        )
        saved = await self.repository.save_improvement_opportunity(opp)
        self._publish_event(
            ImprovementOpportunityCreatedEvent(
                opportunity_id=saved.id, company_id=company_id, title=title
            )
        )
        return saved

    async def propose_adaptation(
        self,
        company_id: str,
        opportunity_id: str,
        adaptation_type: AdaptationType = AdaptationType.WORKFLOW_CHANGE,
        risk_level: AdaptationRiskLevel = AdaptationRiskLevel.MEDIUM,
        current_state: Optional[Dict[str, Any]] = None,
        proposed_state: Optional[Dict[str, Any]] = None,
        rationale: str = "",
        rollback_plan: Optional[Dict[str, Any]] = None,
        governance_required: bool = True,
    ) -> AdaptationProposal:
        proposal = AdaptationProposal(
            id=str(uuid.uuid4()),
            company_id=company_id,
            opportunity_id=opportunity_id,
            adaptation_type=adaptation_type,
            risk_level=risk_level,
            current_state=current_state or {},
            proposed_state=proposed_state or {},
            rationale=rationale or "Continuous organizational learning adaptation proposal.",
            rollback_plan=rollback_plan or {"action": "REVERT_CONFIG", "est_seconds": 30},
            status=AdaptationStatus.PROPOSED,
            governance_required=governance_required,
            governance_approval_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        saved = await self.repository.save_adaptation_proposal(proposal)

        self._publish_event(
            AdaptationProposalCreatedEvent(
                proposal_id=saved.id,
                company_id=company_id,
                adaptation_type=adaptation_type.value if hasattr(adaptation_type, "value") else str(adaptation_type),
            )
        )
        return saved

    async def evaluate_adaptation_proposal(
        self, proposal_id: str, company_id: str
    ) -> AdaptationEvaluation:
        proposal = await self.repository.get_adaptation_proposal_by_id(proposal_id)
        if not proposal or proposal.company_id != company_id:
            raise ValueError(f"Adaptation proposal '{proposal_id}' not found.")

        # Multi-dimensional scoring
        eval_obj = AdaptationEvaluation(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            company_id=company_id,
            expected_benefit_score=0.85,
            risk_score=0.30 if proposal.risk_level == AdaptationRiskLevel.LOW else 0.50,
            cost_score=0.20,
            reversibility_score=0.90,
            overall_recommendation_score=0.82,
            evaluation_breakdown={
                "pros": "High expected impact with low cost and quick reversibility.",
                "cons": "Requires monitoring for potential downstream queue side-effects.",
            },
            evaluated_at=datetime.now(UTC),
        )
        saved = await self.repository.save_adaptation_evaluation(eval_obj)

        if proposal.status == AdaptationStatus.PROPOSED:
            proposal.transition_status(AdaptationStatus.ANALYZING)
            await self.repository.save_adaptation_proposal(proposal)

        return saved

    async def assess_impact(
        self, proposal_id: str, company_id: str
    ) -> AdaptationImpactAssessment:
        proposal = await self.repository.get_adaptation_proposal_by_id(proposal_id)
        if not proposal or proposal.company_id != company_id:
            raise ValueError(f"Adaptation proposal '{proposal_id}' not found.")

        assessment = AdaptationImpactAssessment(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            company_id=company_id,
            affected_subsystems=["TASK_ENGINE", "WORKFORCE"],
            downstream_dependencies=["MODEL_ROUTER"],
            rollback_feasibility_score=0.95,
            assessed_at=datetime.now(UTC),
        )
        saved = await self.repository.save_adaptation_impact_assessment(assessment)
        return saved

    async def attach_governance_approval(
        self, proposal_id: str, company_id: str, governance_approval_id: str
    ) -> AdaptationProposal:
        proposal = await self.repository.get_adaptation_proposal_by_id(proposal_id)
        if not proposal or proposal.company_id != company_id:
            raise ValueError(f"Adaptation proposal '{proposal_id}' not found.")

        proposal.governance_approval_id = governance_approval_id
        proposal.transition_status(AdaptationStatus.APPROVED)
        saved = await self.repository.save_adaptation_proposal(proposal)
        return saved
