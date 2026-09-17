"""
Application Service for Phase 28 Venture Proposal Construction, Innovation Review & Governance Bridge.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.venture import (
    InnovationReview,
    VentureProposal,
    VentureType,
    ProposalStatus,
    VentureResourceRequest,
    VentureResourceConflict,
)
from src.domain.repository import VentureRepositoryInterface


class VentureProposalService:
    """Manages innovation reviews, venture proposal generation, governance approvals, and resource requests."""

    def __init__(
        self,
        repository: VentureRepositoryInterface,
        governance_service: Optional[Any] = None,
        outbox_publisher: Optional[Any] = None,
    ) -> None:
        self.repository = repository
        self.governance_service = governance_service
        self.outbox_publisher = outbox_publisher

    async def generate_innovation_review(
        self,
        company_id: str,
        proposal_id: str,
        strategic_fit_score: float = 0.85,
        customer_value_score: float = 0.90,
        technical_feasibility_score: float = 0.80,
        economic_viability_score: float = 0.75,
        risk_score: float = 0.30,
    ) -> InnovationReview:
        prop = await self.repository.get_proposal_by_id(proposal_id)
        if not prop or prop.company_id != company_id:
            raise ValueError(f"Venture proposal '{proposal_id}' not found.")

        overall = round(
            (strategic_fit_score * 0.25)
            + (customer_value_score * 0.25)
            + (technical_feasibility_score * 0.20)
            + (economic_viability_score * 0.20)
            + ((1.0 - risk_score) * 0.10),
            4,
        )

        review = InnovationReview(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            company_id=company_id,
            strategic_fit_score=strategic_fit_score,
            customer_value_score=customer_value_score,
            technical_feasibility_score=technical_feasibility_score,
            economic_viability_score=economic_viability_score,
            risk_score=risk_score,
            overall_score=overall,
            recommendation="PROCEED_TO_GOVERNANCE" if overall >= 0.70 else "REVISE_OR_REJECT",
            reviewed_at=datetime.now(UTC),
        )
        return await self.repository.save_review(review)

    async def propose_venture(
        self,
        company_id: str,
        opportunity_id: str,
        business_case_id: str,
        title: str,
        venture_type: VentureType = VentureType.NEW_COMPANY,
        required_budget_usd: int = 15000000,
        required_workforce_count: int = 4,
        risk_level: str = "MEDIUM",
        governance_required: bool = True,
    ) -> VentureProposal:
        proposal = VentureProposal(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            company_id=company_id,
            title=title,
            venture_type=venture_type,
            business_case_id=business_case_id,
            required_budget_usd=required_budget_usd,
            required_workforce_count=required_workforce_count,
            risk_level=risk_level,
            status=ProposalStatus.PROPOSED,
            governance_required=governance_required,
            governance_approval_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return await self.repository.save_proposal(proposal)

    async def submit_to_governance(
        self,
        proposal_id: str,
        company_id: str,
        submitted_by: str = "InnovationEngineAI",
    ) -> VentureProposal:
        prop = await self.repository.get_proposal_by_id(proposal_id)
        if not prop or prop.company_id != company_id:
            raise ValueError(f"Venture proposal '{proposal_id}' not found.")

        prop.transition_status(ProposalStatus.GOVERNANCE_PENDING)
        return await self.repository.save_proposal(prop)

    async def attach_governance_approval(
        self,
        proposal_id: str,
        company_id: str,
        governance_approval_id: str,
        governor_id: str = "CHAIRMAN_HUMAN_GOVERNOR",
    ) -> VentureProposal:
        prop = await self.repository.get_proposal_by_id(proposal_id)
        if not prop or prop.company_id != company_id:
            raise ValueError(f"Venture proposal '{proposal_id}' not found.")

        prop.governance_approval_id = governance_approval_id
        if prop.status == ProposalStatus.GOVERNANCE_PENDING or prop.status == ProposalStatus.UNDER_REVIEW:
            prop.transition_status(ProposalStatus.APPROVED)

        return await self.repository.save_proposal(prop)

    async def reject_proposal(
        self,
        proposal_id: str,
        company_id: str,
        reason: str = "Rejected by Human Governance Council",
    ) -> VentureProposal:
        prop = await self.repository.get_proposal_by_id(proposal_id)
        if not prop or prop.company_id != company_id:
            raise ValueError(f"Venture proposal '{proposal_id}' not found.")

        prop.transition_status(ProposalStatus.REJECTED)
        return await self.repository.save_proposal(prop)

    async def request_resources(
        self,
        company_id: str,
        proposal_id: str,
        workforce_count: int = 3,
        model_budget_usd: int = 500000,
        storage_gb: int = 100,
        compute_cores: int = 16,
    ) -> VentureResourceRequest:
        req = VentureResourceRequest(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            company_id=company_id,
            workforce_count=workforce_count,
            model_budget_usd=model_budget_usd,
            storage_gb=storage_gb,
            compute_cores=compute_cores,
            status="PENDING",
            created_at=datetime.now(UTC),
        )
        return await self.repository.save_resource_request(req)
