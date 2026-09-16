"""
Central Application Service Facade for Phase 24 Product, Customer & GTM Operations.

Orchestrates the complete GTM operating loop:
Strategy -> Product -> Market -> Leads -> Opportunities -> Governance -> Proposals -> Orders (Phase 23) -> Onboarding -> Support -> Customer Outcomes -> Product Feedback -> Company Learning.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.gtm import (
    Product,
    Customer,
    Lead,
    Opportunity,
    Proposal,
    SupportCase,
    MarketingCampaign,
    ProductRequirement,
    ProductFeedback,
    CustomerOnboardingPlan,
    OpportunityStage,
    CustomerLifecycleState,
    SupportPriority,
)
from src.domain.repository import GTMRepositoryInterface
from src.application.product_management_service import ProductManagementService
from src.application.crm_sales_service import CRMSalesService
from src.application.customer_success_support_service import CustomerSuccessSupportService
from src.application.marketing_campaign_service import MarketingCampaignService
from src.application.business_operations_service import BusinessOperationsService


class GTMOperationsService:
    """Central orchestration facade for Product, Customer & GTM operations."""

    def __init__(
        self,
        gtm_repository: GTMRepositoryInterface,
        business_service: Optional[BusinessOperationsService] = None,
        outbox_publisher: Optional[Any] = None,
    ) -> None:
        self.repository = gtm_repository
        self.business_service = business_service
        self.product_service = ProductManagementService(gtm_repository, outbox_publisher)
        self.crm_service = CRMSalesService(gtm_repository, outbox_publisher)
        self.customer_service = CustomerSuccessSupportService(gtm_repository, outbox_publisher)
        self.marketing_service = MarketingCampaignService(gtm_repository, outbox_publisher)

    async def execute_deal_won_and_onboard(
        self,
        opportunity_id: str,
        actor_id: str,
        governance_approval_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates the commercial transition when an Opportunity is WON:
        1. Opportunity Stage -> WON
        2. Customer created/activated
        3. Phase 23 Business Operations: Create Invoice & Payment
        4. Customer Onboarding Plan initiated
        """
        # 1. Advance Opportunity Stage
        opp = await self.crm_service.advance_opportunity_stage(opportunity_id, OpportunityStage.WON)

        # 2. Get Lead / Customer
        customer_name = opp.title.replace(" Deal", "").replace(" Proposal", "")
        customer = await self.customer_service.create_customer_from_opportunity(
            name=customer_name,
            domain=f"{customer_name.lower().replace(' ', '')}.com",
            segment="ENTERPRISE",
            account_manager_id=opp.owner_id,
        )

        # 3. Integrate with Phase 23 Business Operations if available
        invoice_id = None
        payment_id = None
        if self.business_service:
            inv = await self.business_service.create_invoice(
                customer_id=customer.id,
                lines=[{"description": f"Product Subscription ({opp.title})", "quantity": 1, "unit_price_cents": opp.estimated_value_cents}],
                currency=opp.currency,
                actor_id=actor_id,
            )
            invoice_id = inv.id
            issued_inv = await self.business_service.issue_and_send_invoice(inv.id, actor_id, governance_approval_id or "GOV-AUTO-WON")
            pmt = await self.business_service.record_payment(
                counterparty=customer.name,
                amount_cents=opp.estimated_value_cents,
                currency=opp.currency,
                invoice_id=inv.id,
                governance_approval_id=governance_approval_id or "GOV-AUTO-WON",
                actor_id=actor_id,
            )
            payment_id = pmt.id

        # 4. Initiate Onboarding Plan
        onboarding = await self.customer_service.initiate_onboarding(customer.id, order_id=invoice_id)

        return {
            "opportunity_id": opp.id,
            "customer_id": customer.id,
            "customer_name": customer.name,
            "invoice_id": invoice_id,
            "payment_id": payment_id,
            "onboarding_id": onboarding.id,
            "status": "WON_AND_ONBOARDING_INITIATED",
        }
