"""
SQLAlchemy Async Repository implementation for Phase 24 Product, Customer & GTM Operations.
"""

from collections.abc import Sequence
from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repository import GTMRepositoryInterface
from src.domain.gtm import (
    Product,
    ProductVersion,
    ProductRoadmap,
    ProductRequirement,
    ProductFeedback,
    Customer,
    CustomerContact,
    CustomerInteraction,
    CustomerHealthSnapshot,
    CustomerOutcome,
    Lead,
    Opportunity,
    SalesActivity,
    Proposal,
    CustomerOnboardingPlan,
    SupportCase,
    MarketingCampaign,
    MarketingAsset,
    CommunicationPreference,
    GTMMetric,
    ProductLifecycle,
    CustomerLifecycleState,
    LeadStatus,
    OpportunityStage,
    ProposalStatus,
    SupportCaseStatus,
    SupportPriority,
    CampaignStatus,
    FeedbackCategory,
)
from src.infrastructure.models.gtm_model import (
    ProductModel,
    ProductVersionModel,
    ProductRoadmapModel,
    ProductRequirementModel,
    ProductFeedbackModel,
    CustomerModel,
    CustomerContactModel,
    CustomerInteractionModel,
    CustomerHealthSnapshotModel,
    CustomerOutcomeModel,
    LeadModel,
    OpportunityModel,
    SalesActivityModel,
    ProposalModel,
    CustomerOnboardingPlanModel,
    SupportCaseModel,
    MarketingCampaignModel,
    MarketingAssetModel,
    CommunicationPreferenceModel,
    GTMMetricModel,
)


class SQLAlchemyGTMRepository(GTMRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Product ---
    async def save_product(self, product: Product) -> Product:
        stmt = select(ProductModel).where(ProductModel.id == product.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = ProductModel(
                id=product.id,
                name=product.name,
                code=product.code,
                description=product.description,
                category=product.category,
                lifecycle=product.lifecycle.value if hasattr(product.lifecycle, "value") else str(product.lifecycle),
                owner_employee_id=product.owner_employee_id,
                target_market=product.target_market,
                base_price_cents=product.base_price_cents,
                currency=product.currency,
                metadata_json=product.metadata,
                created_at=product.created_at,
            )
            self.session.add(m)
        else:
            m.lifecycle = product.lifecycle.value if hasattr(product.lifecycle, "value") else str(product.lifecycle)
            m.base_price_cents = product.base_price_cents
            m.metadata_json = product.metadata

        await self.session.commit()
        return product

    async def get_product_by_id(self, product_id: str) -> Optional[Product]:
        stmt = select(ProductModel).where(ProductModel.id == product_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return Product(
            id=m.id,
            name=m.name,
            code=m.code,
            description=m.description,
            category=m.category,
            lifecycle=ProductLifecycle(m.lifecycle),
            owner_employee_id=m.owner_employee_id,
            target_market=m.target_market,
            base_price_cents=m.base_price_cents,
            currency=m.currency,
            metadata=m.metadata_json or {},
            created_at=m.created_at,
        )

    async def list_products(self) -> List[Product]:
        stmt = select(ProductModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            Product(
                id=m.id,
                name=m.name,
                code=m.code,
                description=m.description,
                category=m.category,
                lifecycle=ProductLifecycle(m.lifecycle),
                owner_employee_id=m.owner_employee_id,
                target_market=m.target_market,
                base_price_cents=m.base_price_cents,
                currency=m.currency,
                metadata=m.metadata_json or {},
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Product Requirements & Feedback ---
    async def save_product_requirement(self, req: ProductRequirement) -> ProductRequirement:
        stmt = select(ProductRequirementModel).where(ProductRequirementModel.id == req.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = ProductRequirementModel(
                id=req.id,
                product_id=req.product_id,
                title=req.title,
                user_story=req.user_story,
                priority=req.priority,
                source_feedback_id=req.source_feedback_id,
                task_id=req.task_id,
                status=req.status,
                created_at=req.created_at,
            )
            self.session.add(m)
        else:
            m.status = req.status
            m.task_id = req.task_id

        await self.session.commit()
        return req

    async def list_product_requirements(self, product_id: str) -> List[ProductRequirement]:
        stmt = select(ProductRequirementModel).where(ProductRequirementModel.product_id == product_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ProductRequirement(
                id=m.id,
                product_id=m.product_id,
                title=m.title,
                user_story=m.user_story,
                priority=m.priority,
                source_feedback_id=m.source_feedback_id,
                task_id=m.task_id,
                status=m.status,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def save_product_feedback(self, fb: ProductFeedback) -> ProductFeedback:
        stmt = select(ProductFeedbackModel).where(ProductFeedbackModel.id == fb.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = ProductFeedbackModel(
                id=fb.id,
                product_id=fb.product_id,
                customer_id=fb.customer_id,
                category=fb.category.value if hasattr(fb.category, "value") else str(fb.category),
                summary=fb.summary,
                raw_content=fb.raw_content,
                importance_score=fb.importance_score,
                validated_insight=fb.validated_insight,
                status=fb.status,
                created_at=fb.created_at,
            )
            self.session.add(m)
        else:
            m.validated_insight = fb.validated_insight
            m.status = fb.status

        await self.session.commit()
        return fb

    async def list_product_feedback(self, product_id: str) -> List[ProductFeedback]:
        stmt = select(ProductFeedbackModel).where(ProductFeedbackModel.product_id == product_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            ProductFeedback(
                id=m.id,
                product_id=m.product_id,
                customer_id=m.customer_id,
                category=FeedbackCategory(m.category),
                summary=m.summary,
                raw_content=m.raw_content,
                importance_score=m.importance_score,
                validated_insight=m.validated_insight,
                status=m.status,
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Customer ---
    async def save_customer(self, customer: Customer) -> Customer:
        stmt = select(CustomerModel).where(CustomerModel.id == customer.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = CustomerModel(
                id=customer.id,
                name=customer.name,
                domain=customer.domain,
                segment=customer.segment,
                lifecycle_state=customer.lifecycle_state.value if hasattr(customer.lifecycle_state, "value") else str(customer.lifecycle_state),
                account_manager_id=customer.account_manager_id,
                health_score=customer.health_score,
                created_at=customer.created_at,
                metadata_json=customer.metadata,
            )
            self.session.add(m)
        else:
            m.lifecycle_state = customer.lifecycle_state.value if hasattr(customer.lifecycle_state, "value") else str(customer.lifecycle_state)
            m.health_score = customer.health_score
            m.metadata_json = customer.metadata

        await self.session.commit()
        return customer

    async def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        stmt = select(CustomerModel).where(CustomerModel.id == customer_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return Customer(
            id=m.id,
            name=m.name,
            domain=m.domain,
            segment=m.segment,
            lifecycle_state=CustomerLifecycleState(m.lifecycle_state),
            account_manager_id=m.account_manager_id,
            health_score=m.health_score,
            created_at=m.created_at,
            metadata=m.metadata_json or {},
        )

    async def list_customers(self) -> List[Customer]:
        stmt = select(CustomerModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            Customer(
                id=m.id,
                name=m.name,
                domain=m.domain,
                segment=m.segment,
                lifecycle_state=CustomerLifecycleState(m.lifecycle_state),
                account_manager_id=m.account_manager_id,
                health_score=m.health_score,
                created_at=m.created_at,
                metadata=m.metadata_json or {},
            )
            for m in models
        ]

    # --- Customer Interactions ---
    async def save_customer_interaction(self, inter: CustomerInteraction) -> CustomerInteraction:
        stmt = select(CustomerInteractionModel).where(CustomerInteractionModel.id == inter.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = CustomerInteractionModel(
                id=inter.id,
                customer_id=inter.customer_id,
                contact_id=inter.contact_id,
                interaction_type=inter.interaction_type,
                channel=inter.channel,
                summary=inter.summary,
                actor_id=inter.actor_id,
                occurred_at=inter.occurred_at,
                provenance_reference=inter.provenance_reference,
            )
            self.session.add(m)

        await self.session.commit()
        return inter

    async def list_customer_interactions(self, customer_id: str) -> List[CustomerInteraction]:
        stmt = select(CustomerInteractionModel).where(CustomerInteractionModel.customer_id == customer_id)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            CustomerInteraction(
                id=m.id,
                customer_id=m.customer_id,
                contact_id=m.contact_id,
                interaction_type=m.interaction_type,
                channel=m.channel,
                summary=m.summary,
                actor_id=m.actor_id,
                occurred_at=m.occurred_at,
                provenance_reference=m.provenance_reference,
            )
            for m in models
        ]

    # --- Leads & Opportunities ---
    async def save_lead(self, lead: Lead) -> Lead:
        stmt = select(LeadModel).where(LeadModel.id == lead.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = LeadModel(
                id=lead.id,
                company_name=lead.company_name,
                contact_name=lead.contact_name,
                contact_email=lead.contact_email,
                source=lead.source,
                status=lead.status.value if hasattr(lead.status, "value") else str(lead.status),
                score=lead.score,
                assigned_owner_id=lead.assigned_owner_id,
                created_at=lead.created_at,
            )
            self.session.add(m)
        else:
            m.status = lead.status.value if hasattr(lead.status, "value") else str(lead.status)
            m.score = lead.score

        await self.session.commit()
        return lead

    async def get_lead_by_id(self, lead_id: str) -> Optional[Lead]:
        stmt = select(LeadModel).where(LeadModel.id == lead_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return Lead(
            id=m.id,
            company_name=m.company_name,
            contact_name=m.contact_name,
            contact_email=m.contact_email,
            source=m.source,
            status=LeadStatus(m.status),
            score=m.score,
            assigned_owner_id=m.assigned_owner_id,
            created_at=m.created_at,
        )

    async def list_leads(self) -> List[Lead]:
        stmt = select(LeadModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            Lead(
                id=m.id,
                company_name=m.company_name,
                contact_name=m.contact_name,
                contact_email=m.contact_email,
                source=m.source,
                status=LeadStatus(m.status),
                score=m.score,
                assigned_owner_id=m.assigned_owner_id,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def save_opportunity(self, opp: Opportunity) -> Opportunity:
        stmt = select(OpportunityModel).where(OpportunityModel.id == opp.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = OpportunityModel(
                id=opp.id,
                lead_id=opp.lead_id,
                customer_id=opp.customer_id,
                title=opp.title,
                product_id=opp.product_id,
                stage=opp.stage.value if hasattr(opp.stage, "value") else str(opp.stage),
                estimated_value_cents=opp.estimated_value_cents,
                currency=opp.currency,
                probability_pct=opp.probability_pct,
                owner_id=opp.owner_id,
                expected_close_date=opp.expected_close_date,
                created_at=opp.created_at,
            )
            self.session.add(m)
        else:
            m.stage = opp.stage.value if hasattr(opp.stage, "value") else str(opp.stage)
            m.probability_pct = opp.probability_pct
            m.estimated_value_cents = opp.estimated_value_cents

        await self.session.commit()
        return opp

    async def get_opportunity_by_id(self, opp_id: str) -> Optional[Opportunity]:
        stmt = select(OpportunityModel).where(OpportunityModel.id == opp_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return Opportunity(
            id=m.id,
            lead_id=m.lead_id,
            customer_id=m.customer_id,
            title=m.title,
            product_id=m.product_id,
            stage=OpportunityStage(m.stage),
            estimated_value_cents=m.estimated_value_cents,
            currency=m.currency,
            probability_pct=m.probability_pct,
            owner_id=m.owner_id,
            expected_close_date=m.expected_close_date,
            created_at=m.created_at,
        )

    async def list_opportunities(self) -> List[Opportunity]:
        stmt = select(OpportunityModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            Opportunity(
                id=m.id,
                lead_id=m.lead_id,
                customer_id=m.customer_id,
                title=m.title,
                product_id=m.product_id,
                stage=OpportunityStage(m.stage),
                estimated_value_cents=m.estimated_value_cents,
                currency=m.currency,
                probability_pct=m.probability_pct,
                owner_id=m.owner_id,
                expected_close_date=m.expected_close_date,
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Proposals ---
    async def save_proposal(self, prop: Proposal) -> Proposal:
        stmt = select(ProposalModel).where(ProposalModel.id == prop.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = ProposalModel(
                id=prop.id,
                opportunity_id=prop.opportunity_id,
                title=prop.title,
                product_id=prop.product_id,
                base_amount_cents=prop.base_amount_cents,
                discount_pct=prop.discount_pct,
                total_amount_cents=prop.total_amount_cents,
                currency=prop.currency,
                status=prop.status.value if hasattr(prop.status, "value") else str(prop.status),
                governance_approval_id=prop.governance_approval_id,
                owner_id=prop.owner_id,
                valid_until=prop.valid_until,
            )
            self.session.add(m)
        else:
            m.status = prop.status.value if hasattr(prop.status, "value") else str(prop.status)
            m.governance_approval_id = prop.governance_approval_id

        await self.session.commit()
        return prop

    async def get_proposal_by_id(self, prop_id: str) -> Optional[Proposal]:
        stmt = select(ProposalModel).where(ProposalModel.id == prop_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return Proposal(
            id=m.id,
            opportunity_id=m.opportunity_id,
            title=m.title,
            product_id=m.product_id,
            base_amount_cents=m.base_amount_cents,
            discount_pct=m.discount_pct,
            total_amount_cents=m.total_amount_cents,
            currency=m.currency,
            status=ProposalStatus(m.status),
            governance_approval_id=m.governance_approval_id,
            owner_id=m.owner_id,
            valid_until=m.valid_until,
        )

    async def list_proposals(self) -> List[Proposal]:
        stmt = select(ProposalModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            Proposal(
                id=m.id,
                opportunity_id=m.opportunity_id,
                title=m.title,
                product_id=m.product_id,
                base_amount_cents=m.base_amount_cents,
                discount_pct=m.discount_pct,
                total_amount_cents=m.total_amount_cents,
                currency=m.currency,
                status=ProposalStatus(m.status),
                governance_approval_id=m.governance_approval_id,
                owner_id=m.owner_id,
                valid_until=m.valid_until,
            )
            for m in models
        ]

    # --- Support Cases ---
    async def save_support_case(self, case: SupportCase) -> SupportCase:
        stmt = select(SupportCaseModel).where(SupportCaseModel.id == case.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = SupportCaseModel(
                id=case.id,
                customer_id=case.customer_id,
                subject=case.subject,
                description=case.description,
                priority=case.priority.value if hasattr(case.priority, "value") else str(case.priority),
                status=case.status.value if hasattr(case.status, "value") else str(case.status),
                assigned_employee_id=case.assigned_employee_id,
                escalated_task_id=case.escalated_task_id,
                resolution_notes=case.resolution_notes,
                created_at=case.created_at,
            )
            self.session.add(m)
        else:
            m.status = case.status.value if hasattr(case.status, "value") else str(case.status)
            m.escalated_task_id = case.escalated_task_id
            m.resolution_notes = case.resolution_notes

        await self.session.commit()
        return case

    async def get_support_case_by_id(self, case_id: str) -> Optional[SupportCase]:
        stmt = select(SupportCaseModel).where(SupportCaseModel.id == case_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return SupportCase(
            id=m.id,
            customer_id=m.customer_id,
            subject=m.subject,
            description=m.description,
            priority=SupportPriority(m.priority),
            status=SupportCaseStatus(m.status),
            assigned_employee_id=m.assigned_employee_id,
            escalated_task_id=m.escalated_task_id,
            resolution_notes=m.resolution_notes,
            created_at=m.created_at,
        )

    async def list_support_cases(self) -> List[SupportCase]:
        stmt = select(SupportCaseModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            SupportCase(
                id=m.id,
                customer_id=m.customer_id,
                subject=m.subject,
                description=m.description,
                priority=SupportPriority(m.priority),
                status=SupportCaseStatus(m.status),
                assigned_employee_id=m.assigned_employee_id,
                escalated_task_id=m.escalated_task_id,
                resolution_notes=m.resolution_notes,
                created_at=m.created_at,
            )
            for m in models
        ]

    # --- Marketing Campaigns ---
    async def save_marketing_campaign(self, campaign: MarketingCampaign) -> MarketingCampaign:
        stmt = select(MarketingCampaignModel).where(MarketingCampaignModel.id == campaign.id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()

        if m is None:
            m = MarketingCampaignModel(
                id=campaign.id,
                name=campaign.name,
                objective=campaign.objective,
                target_audience=campaign.target_audience,
                channel=campaign.channel,
                budget_cents=campaign.budget_cents,
                spent_cents=campaign.spent_cents,
                currency=campaign.currency,
                status=campaign.status.value if hasattr(campaign.status, "value") else str(campaign.status),
                governance_approval_id=campaign.governance_approval_id,
                owner_id=campaign.owner_id,
                started_at=campaign.started_at,
                ended_at=campaign.ended_at,
            )
            self.session.add(m)
        else:
            m.status = campaign.status.value if hasattr(campaign.status, "value") else str(campaign.status)
            m.spent_cents = campaign.spent_cents

        await self.session.commit()
        return campaign

    async def get_marketing_campaign_by_id(self, campaign_id: str) -> Optional[MarketingCampaign]:
        stmt = select(MarketingCampaignModel).where(MarketingCampaignModel.id == campaign_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return MarketingCampaign(
            id=m.id,
            name=m.name,
            objective=m.objective,
            target_audience=m.target_audience,
            channel=m.channel,
            budget_cents=m.budget_cents,
            spent_cents=m.spent_cents,
            currency=m.currency,
            status=CampaignStatus(m.status),
            governance_approval_id=m.governance_approval_id,
            owner_id=m.owner_id,
            started_at=m.started_at,
            ended_at=m.ended_at,
        )

    async def list_marketing_campaigns(self) -> List[MarketingCampaign]:
        stmt = select(MarketingCampaignModel)
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            MarketingCampaign(
                id=m.id,
                name=m.name,
                objective=m.objective,
                target_audience=m.target_audience,
                channel=m.channel,
                budget_cents=m.budget_cents,
                spent_cents=m.spent_cents,
                currency=m.currency,
                status=CampaignStatus(m.status),
                governance_approval_id=m.governance_approval_id,
                owner_id=m.owner_id,
                started_at=m.started_at,
                ended_at=m.ended_at,
            )
            for m in models
        ]
