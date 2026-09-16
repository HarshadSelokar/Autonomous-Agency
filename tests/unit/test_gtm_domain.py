"""
Unit tests for Phase 24 Product, Customer & GTM domain models.
"""

import pytest

from src.domain.gtm import (
    Product,
    ProductLifecycle,
    Customer,
    CustomerLifecycleState,
    Lead,
    LeadStatus,
    Opportunity,
    OpportunityStage,
    Proposal,
    ProposalStatus,
    SupportCase,
    SupportCaseStatus,
    SupportPriority,
    MarketingCampaign,
    CampaignStatus,
    FeedbackCategory,
)
from src.domain.exceptions import PricingPolicyViolationError, CustomerDataIsolationError


def test_product_and_customer_models() -> None:
    prod = Product(
        name="Enterprise AI Swarm Engine",
        code="PROD-SWARM-01",
        lifecycle=ProductLifecycle.ACTIVE,
        base_price_cents=1000000, # $10,000
    )
    assert prod.money_base_price.to_dollars() == 10000.0

    cust = Customer(
        name="Acme Corp",
        domain="acme.com",
        lifecycle_state=CustomerLifecycleState.CUSTOMER,
    )
    assert cust.name == "Acme Corp"
    assert cust.lifecycle_state == CustomerLifecycleState.CUSTOMER


def test_proposal_discount_calculation() -> None:
    prop = Proposal(
        title="Enterprise AI OS Proposal",
        base_amount_cents=1000000, # $10,000
        discount_pct=10.0,
    )
    total = prop.calculate_total()
    assert total == 900000 # 10% off $10,000 = $9,000 (900,000 cents)

    # Invalid discount percentage raises PricingPolicyViolationError
    prop_invalid = Proposal(
        title="Invalid Discount Proposal",
        base_amount_cents=1000000,
        discount_pct=150.0,
    )
    with pytest.raises(PricingPolicyViolationError):
        prop_invalid.calculate_total()


def test_support_case_model() -> None:
    case = SupportCase(
        customer_id="cust-123",
        subject="API Rate Limit Exceeded",
        priority=SupportPriority.HIGH,
        status=SupportCaseStatus.OPEN,
    )
    assert case.priority == SupportPriority.HIGH
    assert case.status == SupportCaseStatus.OPEN
