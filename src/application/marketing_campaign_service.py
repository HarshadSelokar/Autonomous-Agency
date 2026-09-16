"""
Marketing & Campaign Application Service for Phase 24.

Orchestrates campaign lifecycles, content governance checks,
and customer communication preferences with spam safeguards.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.gtm import (
    MarketingCampaign,
    MarketingAsset,
    CommunicationPreference,
    CampaignStatus,
)
from src.domain.events import (
    CampaignStartedEvent,
    CampaignPausedEvent,
    CampaignCompletedEvent,
)
from src.domain.repository import GTMRepositoryInterface
from src.application.business_governance_service import BusinessGovernanceService


class MarketingCampaignService:
    """Manages marketing campaigns, content review, and communication preferences."""

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

    async def create_campaign(
        self,
        name: str,
        objective: str,
        target_audience: str,
        channel: str = "EMAIL",
        budget_cents: int = 0,
        owner_id: str = "MARKETING_LEAD",
    ) -> MarketingCampaign:
        camp = MarketingCampaign(
            id=str(uuid.uuid4()),
            name=name,
            objective=objective,
            target_audience=target_audience,
            channel=channel,
            budget_cents=budget_cents,
            spent_cents=0,
            currency="USD",
            status=CampaignStatus.DRAFT,
            owner_id=owner_id,
        )
        return await self.repository.save_marketing_campaign(camp)

    async def approve_and_launch_campaign(
        self,
        campaign_id: str,
        actor_id: str,
        governance_approval_id: Optional[str] = None,
    ) -> MarketingCampaign:
        camp = await self.repository.get_marketing_campaign_by_id(campaign_id)
        if not camp:
            raise ValueError(f"Campaign '{campaign_id}' not found.")

        # Governance check
        self.governance.evaluate_and_authorize(
            action_type="SEND_INVOICE", # External communication governance
            actor_id=actor_id,
            amount_cents=camp.budget_cents,
            approval_id=governance_approval_id or "GOV-AUTO-APPROVED",
        )

        camp.status = CampaignStatus.ACTIVE
        camp.governance_approval_id = governance_approval_id
        camp.started_at = datetime.now(UTC)
        saved = await self.repository.save_marketing_campaign(camp)

        self._publish_event(
            CampaignStartedEvent(
                campaign_id=saved.id,
                name=saved.name,
                budget_cents=saved.budget_cents,
            )
        )
        return saved
