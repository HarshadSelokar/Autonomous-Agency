"""
CRM & Sales Application Service for Phase 24.

Orchestrates lead management, opportunity pipeline stages, sales activities,
and proposal generation with strict commercial discount governance.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.gtm import (
    Lead,
    Opportunity,
    SalesActivity,
    Proposal,
    LeadStatus,
    OpportunityStage,
    ProposalStatus,
)
from src.domain.events import (
    LeadCreatedEvent,
    LeadQualifiedEvent,
    OpportunityCreatedEvent,
    OpportunityStageChangedEvent,
    ProposalCreatedEvent,
    ProposalApprovedEvent,
    ProposalSentEvent,
)
from src.domain.exceptions import (
    PricingPolicyViolationError,
    UnauthorizedCommercialCommitmentError,
)
from src.domain.repository import GTMRepositoryInterface
from src.application.business_governance_service import BusinessGovernanceService


class CRMSalesService:
    """Manages lead conversion, opportunity pipelines, and commercial proposals."""

    def __init__(
        self,
        repository: GTMRepositoryInterface,
        outbox_publisher: Optional[Any] = None,
        governance_service: Optional[BusinessGovernanceService] = None,
    ) -> None:
        self.repository = repository
        self.outbox_publisher = outbox_publisher
        self.governance = governance_service or BusinessGovernanceService()

    def _publish_event(self, event: Any) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def create_lead(
        self,
        company_name: str,
        contact_name: str,
        contact_email: str,
        source: str = "INBOUND_WEB",
        assigned_owner_id: Optional[str] = None,
    ) -> Lead:
        lead = Lead(
            id=str(uuid.uuid4()),
            company_name=company_name,
            contact_name=contact_name,
            contact_email=contact_email,
            source=source,
            status=LeadStatus.NEW,
            score=10,
            assigned_owner_id=assigned_owner_id,
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_lead(lead)
        self._publish_event(
            LeadCreatedEvent(
                lead_id=saved.id,
                company_name=saved.company_name,
                contact_email=saved.contact_email,
                source=saved.source,
            )
        )
        return saved

    async def qualify_lead(self, lead_id: str, qualified_by: str, score: int = 80) -> Lead:
        lead = await self.repository.get_lead_by_id(lead_id)
        if not lead:
            raise ValueError(f"Lead '{lead_id}' not found.")

        lead.status = LeadStatus.QUALIFIED
        lead.score = score
        saved = await self.repository.save_lead(lead)
        self._publish_event(LeadQualifiedEvent(lead_id=saved.id, qualified_by=qualified_by, score=saved.score))
        return saved

    async def create_opportunity(
        self,
        title: str,
        product_id: str,
        owner_id: str,
        estimated_value_cents: int,
        lead_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        currency: str = "USD",
    ) -> Opportunity:
        opp = Opportunity(
            id=str(uuid.uuid4()),
            lead_id=lead_id,
            customer_id=customer_id,
            title=title,
            product_id=product_id,
            stage=OpportunityStage.QUALIFIED if lead_id else OpportunityStage.IDENTIFIED,
            estimated_value_cents=estimated_value_cents,
            currency=currency,
            probability_pct=30,
            owner_id=owner_id,
            expected_close_date=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        saved = await self.repository.save_opportunity(opp)
        self._publish_event(
            OpportunityCreatedEvent(
                opportunity_id=saved.id,
                lead_id=saved.lead_id,
                customer_id=saved.customer_id,
                estimated_value_cents=saved.estimated_value_cents,
                currency=saved.currency,
                stage=saved.stage.value,
            )
        )
        return saved

    async def advance_opportunity_stage(self, opportunity_id: str, new_stage: OpportunityStage) -> Opportunity:
        opp = await self.repository.get_opportunity_by_id(opportunity_id)
        if not opp:
            raise ValueError(f"Opportunity '{opportunity_id}' not found.")

        prev_stage = opp.stage.value
        opp.stage = new_stage

        if new_stage == OpportunityStage.PROPOSAL:
            opp.probability_pct = 60
        elif new_stage == OpportunityStage.NEGOTIATION:
            opp.probability_pct = 80
        elif new_stage == OpportunityStage.WON:
            opp.probability_pct = 100
        elif new_stage == OpportunityStage.LOST:
            opp.probability_pct = 0

        saved = await self.repository.save_opportunity(opp)
        self._publish_event(
            OpportunityStageChangedEvent(
                opportunity_id=saved.id,
                previous_stage=prev_stage,
                new_stage=saved.stage.value,
            )
        )
        return saved

    async def create_proposal(
        self,
        opportunity_id: str,
        title: str,
        product_id: str,
        base_amount_cents: int,
        owner_id: str,
        discount_pct: float = 0.0,
    ) -> Proposal:
        prop = Proposal(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            title=title,
            product_id=product_id,
            base_amount_cents=base_amount_cents,
            discount_pct=discount_pct,
            currency="USD",
            status=ProposalStatus.DRAFT,
            owner_id=owner_id,
            valid_until=datetime.now(UTC),
        )
        prop.calculate_total()

        # If discount > 15%, requires governance approval
        if discount_pct > 15.0:
            prop.status = ProposalStatus.APPROVAL_REQUIRED

        saved = await self.repository.save_proposal(prop)
        self._publish_event(
            ProposalCreatedEvent(
                proposal_id=saved.id,
                opportunity_id=saved.opportunity_id,
                total_amount_cents=saved.total_amount_cents,
                discount_pct=saved.discount_pct,
            )
        )
        return saved

    async def approve_and_send_proposal(
        self,
        proposal_id: str,
        actor_id: str,
        governance_approval_id: Optional[str] = None,
    ) -> Proposal:
        prop = await self.repository.get_proposal_by_id(proposal_id)
        if not prop:
            raise ValueError(f"Proposal '{proposal_id}' not found.")

        # Governance check: commercial proposals with discount > 15.0% MUST have governance approval
        if prop.discount_pct > 15.0 and not governance_approval_id:
            raise UnauthorizedCommercialCommitmentError(
                f"Proposal '{proposal_id}' discount of {prop.discount_pct}% exceeds 15% policy threshold and requires governance approval."
            )

        # Risk classification
        self.governance.evaluate_and_authorize(
            action_type="SEND_INVOICE", # Maps to commercial commitment risk
            actor_id=actor_id,
            amount_cents=prop.total_amount_cents,
            approval_id=governance_approval_id if prop.discount_pct > 15.0 else "POLICY_AUTO",
        )

        prop.status = ProposalStatus.SENT
        prop.governance_approval_id = governance_approval_id
        saved = await self.repository.save_proposal(prop)

        self._publish_event(
            ProposalApprovedEvent(
                proposal_id=saved.id,
                approved_by=actor_id,
                governance_approval_id=governance_approval_id,
            )
        )
        self._publish_event(ProposalSentEvent(proposal_id=saved.id, sent_to="CUSTOMER"))
        return saved
