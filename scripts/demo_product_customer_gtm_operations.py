"""
Phase 24 End-to-End Demonstration Script: Product, Customer & Go-To-Market Operations.

Demonstrates the complete GTM operating loop:
1. Product Catalog & Release Versioning
2. Lead Ingestion, Qualification & Pipeline Tracking
3. Commercial Proposal Generation, Discount Governance & Approval
4. Deal Closed-Won Execution & Automated Phase 23 Order/Billing/Revenue Integration
5. Automated Onboarding & CS Workspace Setup
6. Support Ticket Handling & Customer Case Resolution
7. Customer Data Isolation & Cross-Tenant Security Verification
8. Marketing Campaign Execution & ROI Analytics
9. Product Feedback Loop & Product Requirement Synthesis
"""

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database import Base
import src.infrastructure.models.gtm_model
import src.infrastructure.models.business_model
from src.infrastructure.repositories.gtm_repository import SQLAlchemyGTMRepository
from src.infrastructure.repositories.business_repository import SQLAlchemyBusinessRepository
from src.application.product_management_service import ProductManagementService
from src.application.crm_sales_service import CRMSalesService
from src.application.customer_success_support_service import CustomerSuccessSupportService
from src.application.marketing_campaign_service import MarketingCampaignService
from src.application.business_operations_service import BusinessOperationsService
from src.application.gtm_operations_service import GTMOperationsService
from src.domain.gtm import (
    OpportunityStage,
    ProposalStatus,
    SupportPriority,
    SupportCaseStatus,
    CampaignStatus,
    FeedbackCategory,
)
from src.domain.exceptions import (
    CustomerDataIsolationError,
    PricingPolicyViolationError,
    UnauthorizedCommercialCommitmentError,
)


async def main():
    print("=" * 80)
    print("PHASE 24: PRODUCT, CUSTOMER & GO-TO-MARKET OPERATIONS DEMONSTRATION")
    print("=" * 80)

    # Setup database engine and session
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_factory() as session:
        # 1. Initialize Repositories and Services
        gtm_repo = SQLAlchemyGTMRepository(session)
        biz_repo = SQLAlchemyBusinessRepository(session)

        product_svc = ProductManagementService(gtm_repo)
        crm_svc = CRMSalesService(gtm_repo)
        cs_svc = CustomerSuccessSupportService(gtm_repo)
        mktg_svc = MarketingCampaignService(gtm_repo)
        biz_svc = BusinessOperationsService(biz_repo)
        gtm_ops_svc = GTMOperationsService(gtm_repo, business_service=biz_svc)

        # --------------------------------------------------------------------------
        # STEP 1: Product Catalog & Release Management
        # --------------------------------------------------------------------------
        print("\n[STEP 1] Creating Product & Release Versioning...")
        product = await product_svc.create_product(
            name="Enterprise Autonomous AI Suite",
            code="PROD-AI-ENT",
            description="Full suite autonomous organization platform for enterprise operations.",
            owner_employee_id="emp-pm-01",
            base_price_cents=2500000  # $25,000.00
        )
        print(f"  [OK] Created Product: {product.name} (Code: {product.code}, Base Price: ${product.base_price_cents/100:.2f})")

        version = await product_svc.release_product_version(
            product_id=product.id,
            version_string="v24.0.0",
            release_notes="Phase 24 Go-To-Market and Customer Success Platform release."
        )
        print(f"  [OK] Released Product Version: {version.version_string} (ID: {version.id})")

        # --------------------------------------------------------------------------
        # STEP 2: Lead Ingestion & Pipeline Tracking
        # --------------------------------------------------------------------------
        print("\n[STEP 2] Ingesting and Qualifying Sales Lead...")
        lead = await crm_svc.create_lead(
            company_name="Acme Tech Corp",
            contact_name="Alice Smith",
            contact_email="alice@acmecorp.com",
            source="INBOUND_WEB",
            score=85
        )
        print(f"  [OK] Ingested Lead: {lead.company_name} ({lead.contact_name}) - Score: {lead.score}, Status: {lead.status.value}")

        opp = await crm_svc.create_opportunity(
            title="Acme Tech Corp Enterprise Deal",
            product_id=product.id,
            owner_id="emp-sales-01",
            estimated_value_cents=2500000,
            lead_id=lead.id
        )
        print(f"  [OK] Created Opportunity: {opp.title} (ID: {opp.id}, Value: ${opp.estimated_value_cents/100:.2f})")

        # --------------------------------------------------------------------------
        # STEP 3: Commercial Proposal & Discount Governance
        # --------------------------------------------------------------------------
        print("\n[STEP 3] Generating Proposal & Enforcing Discount Governance...")
        
        # 10% discount -> automatic approval path
        prop_standard = await crm_svc.create_proposal(
            opportunity_id=opp.id,
            title="Acme Enterprise Standard Proposal",
            product_id=product.id,
            base_amount_cents=2500000,
            owner_id="emp-sales-01",
            discount_pct=10.0
        )
        sent_prop_standard = await crm_svc.approve_and_send_proposal(
            proposal_id=prop_standard.id,
            actor_id="emp-sales-01"
        )
        print(f"  [OK] Standard Proposal (10% discount): Total ${sent_prop_standard.total_amount_cents/100:.2f}, Status: {sent_prop_standard.status.value}")

        # 25% discount -> requires governance approval (>15%)
        prop_high_disc = await crm_svc.create_proposal(
            opportunity_id=opp.id,
            title="Acme Enterprise Custom Proposal",
            product_id=product.id,
            base_amount_cents=2500000,
            owner_id="emp-sales-01",
            discount_pct=25.0
        )
        print(f"  [OK] High-Discount Proposal Created: Discount {prop_high_disc.discount_pct}% (Status: {prop_high_disc.status.value})")

        try:
            await crm_svc.approve_and_send_proposal(
                proposal_id=prop_high_disc.id,
                actor_id="emp-sales-01",
                governance_approval_id=None
            )
            print("  [ERROR] Proposal sent without required governance approval!")
        except UnauthorizedCommercialCommitmentError as e:
            print(f"  [PASSED SECURITY CHECK] Blocked unapproved discount >15%: {e}")

        # Authorize with governance approval ID
        approved_prop = await crm_svc.approve_and_send_proposal(
            proposal_id=prop_high_disc.id,
            actor_id="emp-sales-01",
            governance_approval_id="gov-appr-disc-991"
        )
        print(f"  [OK] Governance Approved & Sent Proposal! Status: {approved_prop.status.value}")

        # --------------------------------------------------------------------------
        # STEP 4: Deal Closed-Won & Phase 23 Integration
        # --------------------------------------------------------------------------
        print("\n[STEP 4] Executing Deal Closed-Won & Phase 23 Business Operations Integration...")
        deal_result = await gtm_ops_svc.execute_deal_won_and_onboard(
            opportunity_id=opp.id,
            actor_id="mgr-sales-lead",
            governance_approval_id="gov-appr-disc-991"
        )

        print(f"  [WON] Deal Closed-Won Result: {deal_result['status']}")
        print(f"  [OK] Customer Created: {deal_result['customer_name']} (ID: {deal_result['customer_id']})")
        print(f"  [OK] Phase 23 Invoice Created: ID {deal_result['invoice_id']}")
        print(f"  [OK] Phase 23 Payment Recorded: ID {deal_result['payment_id']}")
        print(f"  [OK] Customer Onboarding Initiated: Plan ID {deal_result['onboarding_id']}")

        # --------------------------------------------------------------------------
        # STEP 5: Customer Success & Support Case Handling
        # --------------------------------------------------------------------------
        print("\n[STEP 5] Support Ticket Creation & Resolution...")
        customer_id = deal_result['customer_id']

        support_case = await cs_svc.create_support_case(
            customer_id=customer_id,
            subject="API Webhook Integration setup",
            description="Need help setting up realtime event webhooks.",
            priority=SupportPriority.HIGH
        )
        print(f"  [OK] Created Support Case: '{support_case.subject}' (ID: {support_case.id}, Priority: {support_case.priority.value})")

        resolved_case = await cs_svc.resolve_support_case(
            case_id=support_case.id,
            resolved_by_employee_id="emp-support-01",
            resolution_notes="Configured webhook payload endpoint and tested signature validation."
        )
        print(f"  [OK] Resolved Support Case! Status: {resolved_case.status.value}, Resolution: '{resolved_case.resolution_notes}'")

        # --------------------------------------------------------------------------
        # STEP 6: Customer Data Security & Isolation Verification
        # --------------------------------------------------------------------------
        print("\n[STEP 6] Customer Data Isolation Security Verification...")
        try:
            cs_svc.verify_customer_access(
                requestor_customer_id="cust-hacker-tenant-99",
                target_customer_id=customer_id
            )
            print("  [ERROR] Cross-tenant security check failed!")
        except CustomerDataIsolationError as e:
            print(f"  [PASSED ISOLATION CHECK] Access blocked for unauthorized tenant: {e}")

        # --------------------------------------------------------------------------
        # STEP 7: Marketing Campaign & Analytics
        # --------------------------------------------------------------------------
        print("\n[STEP 7] Executing Marketing Campaign & Tracking ROI...")
        campaign = await mktg_svc.create_campaign(
            name="Q4 Enterprise Automation Launch",
            objective="Drive enterprise lead generation for AI suite",
            target_audience="CTOs & VPs of Engineering",
            channel="EMAIL",
            budget_cents=500000,
            owner_id="emp-mktg-01"
        )
        print(f"  [OK] Created Campaign: {campaign.name} (ID: {campaign.id}, Budget: ${campaign.budget_cents/100:.2f})")

        launched_camp = await mktg_svc.launch_campaign(
            campaign_id=campaign.id,
            actor_id="emp-mktg-01",
            governance_approval_id="gov-appr-mktg-01"
        )
        print(f"  [OK] Launched Campaign! Status: {launched_camp.status.value}")

        # --------------------------------------------------------------------------
        # STEP 8: Product Feedback Loop & Requirement Synthesis
        # --------------------------------------------------------------------------
        print("\n[STEP 8] Customer Feedback Collection & Product Requirement Synthesis...")
        feedback = await product_svc.record_customer_feedback(
            product_id=product.id,
            customer_id=customer_id,
            summary="Need custom role-based access control (RBAC)",
            raw_content="We require granular RBAC controls for sub-departments.",
            category=FeedbackCategory.FEATURE_REQUEST,
            importance_score=9
        )
        print(f"  [OK] Recorded Customer Feedback (ID: {feedback.id}, Importance: {feedback.importance_score}/10)")

        requirement = await product_svc.synthesize_feedback_to_requirement(
            feedback_id=feedback.id,
            title="Granular RBAC for Sub-Departments",
            user_story="As an enterprise administrator, I want to define custom RBAC roles per department.",
            priority="HIGH",
            task_id="task-rbac-spec-101"
        )
        print(f"  [OK] Synthesized Feedback into Product Requirement (ID: {requirement.id}, Linked Task: {requirement.task_id})")

        await session.commit()

    await engine.dispose()

    print("\n" + "=" * 80)
    print("[SUCCESS] PHASE 24 GTM OPERATIONS E2E DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
