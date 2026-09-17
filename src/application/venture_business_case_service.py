"""
Application Service for Phase 28 Business Case Construction, Scenario Modeling & Sensitivity Analysis.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
import uuid

from src.domain.venture import (
    ProductConcept,
    BusinessModelConcept,
    VentureBusinessCase,
    BusinessCaseStatus,
)
from src.domain.repository import VentureRepositoryInterface


class VentureBusinessCaseService:
    """Constructs product/business model concepts, financial models, scenario simulations, and sensitivity analyses."""

    def __init__(
        self,
        repository: VentureRepositoryInterface,
        simulation_service: Optional[Any] = None,
        outbox_publisher: Optional[Any] = None,
    ) -> None:
        self.repository = repository
        self.simulation_service = simulation_service
        self.outbox_publisher = outbox_publisher

    async def create_product_concept(
        self,
        company_id: str,
        idea_id: str,
        name: str,
        target_segment: str,
        capabilities: List[str],
        value_proposition: str,
        pricing_hypothesis: Optional[Dict[str, Any]] = None,
        distribution_channel: str = "DIRECT_DIGITAL_SALES",
    ) -> ProductConcept:
        concept = ProductConcept(
            id=str(uuid.uuid4()),
            idea_id=idea_id,
            company_id=company_id,
            name=name,
            target_segment=target_segment,
            capabilities=capabilities,
            value_proposition=value_proposition,
            pricing_hypothesis=pricing_hypothesis or {"tier_basic_usd": 4900, "tier_enterprise_usd": 49900},
            distribution_channel=distribution_channel,
            created_at=datetime.now(UTC),
        )
        return await self.repository.save_product_concept(concept)

    async def create_business_model_concept(
        self,
        company_id: str,
        idea_id: str,
        revenue_model: str = "SUBSCRIPTION",
        pricing_model: Optional[Dict[str, Any]] = None,
        acquisition_strategy: str = "INBOUND_CONTENT_MARKETING",
        cost_structure: Optional[Dict[str, Any]] = None,
        gross_margin_est: float = 0.75,
        operating_model: str = "AUTONOMOUS_SWARM_OPERATIONS",
    ) -> BusinessModelConcept:
        concept = BusinessModelConcept(
            id=str(uuid.uuid4()),
            idea_id=idea_id,
            company_id=company_id,
            revenue_model=revenue_model,
            pricing_model=pricing_model or {"arpu_usd": 500},
            acquisition_strategy=acquisition_strategy,
            cost_structure=cost_structure or {"cac_usd": 1500, "hosting_monthly_usd": 2000},
            gross_margin_est=gross_margin_est,
            operating_model=operating_model,
            created_at=datetime.now(UTC),
        )
        return await self.repository.save_business_model_concept(concept)

    async def construct_business_case(
        self,
        company_id: str,
        opportunity_id: str,
        title: str,
        market_assumptions: Optional[Dict[str, Any]] = None,
        financial_model: Optional[Dict[str, Any]] = None,
        workforce_reqs: Optional[Dict[str, Any]] = None,
        infra_reqs: Optional[Dict[str, Any]] = None,
        risk_analysis: Optional[Dict[str, Any]] = None,
        scenarios: Optional[Dict[str, Any]] = None,
        expected_roi: float = 0.35,
    ) -> VentureBusinessCase:
        opp = await self.repository.get_opportunity_by_id(opportunity_id)
        if not opp or opp.company_id != company_id:
            raise ValueError(f"Innovation opportunity '{opportunity_id}' not found.")

        # Default multi-scenario structure: BASELINE vs CONSERVATIVE vs AGGRESSIVE
        scenarios_payload = scenarios or {
            "BASELINE": {"roi": expected_roi, "arr_usd": 50000000, "payback_months": 8},
            "CONSERVATIVE": {"roi": max(0.05, expected_roi - 0.20), "arr_usd": 25000000, "payback_months": 16},
            "AGGRESSIVE": {"roi": expected_roi + 0.25, "arr_usd": 120000000, "payback_months": 4},
        }

        bcase = VentureBusinessCase(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            company_id=company_id,
            title=title,
            market_assumptions=market_assumptions or {"tam_usd": 1000000000, "sam_usd": 100000000},
            financial_model=financial_model or {"year1_rev_cents": 50000000, "cogs_cents": 12000000},
            workforce_reqs=workforce_reqs or {"engineers": 2, "product_managers": 1, "gtm_agents": 1},
            infra_reqs=infra_reqs or {"cloud_nodes": 4, "model_quota_daily": 50000},
            risk_analysis=risk_analysis or {"execution_risk": "MEDIUM", "competition_risk": "LOW"},
            scenarios=scenarios_payload,
            expected_roi=expected_roi,
            uncertainty_score=0.25,
            status=BusinessCaseStatus.DRAFT,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return await self.repository.save_business_case(bcase)

    async def perform_sensitivity_analysis(
        self,
        business_case_id: str,
        company_id: str,
        key_assumptions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        bcase = await self.repository.get_business_case_by_id(business_case_id)
        if not bcase or bcase.company_id != company_id:
            raise ValueError(f"Venture business case '{business_case_id}' not found.")

        assumptions = key_assumptions or ["cac_usd", "arpu_usd", "gross_margin"]
        sensitivity = {
            "business_case_id": business_case_id,
            "base_roi": bcase.expected_roi,
            "sensitivity_matrix": {
                "cac_plus_20_pct": round(bcase.expected_roi * 0.85, 4),
                "arpu_minus_15_pct": round(bcase.expected_roi * 0.78, 4),
                "gross_margin_minus_10_pct": round(bcase.expected_roi * 0.88, 4),
            },
            "high_sensitivity_variables": ["cac_usd"],
        }
        return sensitivity
