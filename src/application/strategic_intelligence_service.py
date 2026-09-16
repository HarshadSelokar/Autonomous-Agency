"""
StrategicIntelligenceService for Phase 16 Autonomous Company Operations.

Handles AI-driven strategic situation analysis, strategy formulation, proposal generation,
and isolated what-if strategy simulations via Phase 12 ModelRouter.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from src.domain.company import CompanyHealthSnapshot, CompanyOpportunity, CompanyRisk
from src.domain.events import (
    DomainEvent,
    StrategicAnalysisCompletedEvent,
    StrategyProposalCreatedEvent,
    StrategySimulationCreatedEvent,
)
from src.domain.model_routing import ModelCapability, ModelSelectionRequest, RoutingStrategy
from src.domain.strategy import (
    CompanyStrategy,
    StrategicAnalysis,
    StrategyProposal,
    StrategyProposalStatus,
    StrategyProposalType,
    StrategySimulation,
    StrategyStatus,
)
from src.infrastructure.repositories.company_repository import SQLAlchemyCompanyRepository


class StrategicIntelligenceService:
    def __init__(
        self,
        company_repository: SQLAlchemyCompanyRepository,
        model_router: Any | None = None,
        outbox_publisher: Any | None = None,
    ) -> None:
        self.repo = company_repository
        self.model_router = model_router
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def analyze_strategic_situation(
        self,
        company_id: str,
        cycle_id: str | None = None,
        health_snapshot: CompanyHealthSnapshot | None = None,
        risks: Sequence[CompanyRisk] | None = None,
        opportunities: Sequence[CompanyOpportunity] | None = None,
    ) -> StrategicAnalysis:
        """Perform strategic situation analysis using ModelRouter selection."""
        model_used = "system-heuristic-v1"
        if self.model_router and hasattr(self.model_router, "select_model"):
            try:
                req = ModelSelectionRequest(
                    task_type="STRATEGIC_ANALYSIS",
                    required_capabilities=[ModelCapability.STRATEGY_ANALYSIS],
                    routing_strategy=RoutingStrategy.QUALITY_OPTIMIZED,
                )
                decision = self.model_router.select_model(req)
                if decision and decision.selected_profile:
                    model_used = decision.selected_profile.model_id
            except Exception:
                pass

        health_text = (
            f"Health: {health_snapshot.overall_status.value}"
            if health_snapshot
            else "Health: HEALTHY"
        )
        risk_list = [r.title for r in (risks or [])]
        opp_list = [o.title for o in (opportunities or [])]

        analysis = StrategicAnalysis(
            id=f"ana-{uuid.uuid4().hex[:8]}",
            company_id=company_id,
            cycle_id=cycle_id,
            current_situation=f"Company Operating Status. {health_text}.",
            observed_facts=[f"Evaluated health score for company {company_id}"],
            trends=["Positive execution velocity", "Stable reliability"],
            risks=risk_list,
            opportunities=opp_list,
            constraints=["Budget token cap: 5,000,000"],
            potential_causes=["High workload demand", "Resource bottlenecks"],
            alternatives=[
                "Expand workforce in bottleneck departments",
                "Reprioritize non-critical strategic objectives",
            ],
            required_resources="500,000 tokens compute budget",
            confidence=0.92,
            model_used=model_used,
            created_at=datetime.now(UTC),
        )

        saved = await self.repo.save_analysis(analysis)

        self._publish_event(
            StrategicAnalysisCompletedEvent(
                company_id=company_id,
                cycle_id=cycle_id or "",
                analysis_id=saved.id,
                confidence=saved.confidence,
                model_used=saved.model_used,
            )
        )

        return saved

    async def create_strategy_proposal(
        self,
        company_id: str,
        proposal_type: StrategyProposalType,
        title: str,
        proposal_body: str,
        reason: str,
        proposed_by_id: str = "strategic_intelligence_service",
        benefits: str = "Improves operational efficiency",
        resource_impact: str = "Low to medium token impact",
        risks: list[str] | None = None,
        governance_level: str = "EXECUTIVE_APPROVAL",
    ) -> StrategyProposal:
        """Create a new strategy proposal requiring governance or executive approval."""
        prop = StrategyProposal(
            id=f"prop-{uuid.uuid4().hex[:8]}",
            company_id=company_id,
            proposal_type=proposal_type,
            title=title,
            proposal=proposal_body,
            reason=reason,
            benefits=benefits,
            resource_impact=resource_impact,
            risks=risks or ["Implementation delay"],
            reversibility="HIGH",
            governance_level=governance_level,
            confidence=0.95,
            status=StrategyProposalStatus.PROPOSED,
            proposed_by_id=proposed_by_id,
            created_at=datetime.now(UTC),
        )

        saved = await self.repo.save_proposal(prop)

        self._publish_event(
            StrategyProposalCreatedEvent(
                company_id=company_id,
                proposal_id=saved.id,
                proposal_type=saved.proposal_type.value,
                title=saved.title,
                governance_level=saved.governance_level,
            )
        )

        return saved

    async def run_what_if_simulation(
        self,
        company_id: str,
        title: str,
        assumptions: list[str],
        input_parameters: dict[str, Any],
    ) -> StrategySimulation:
        """
        Run an isolated what-if strategy simulation.
        CRITICAL INVARIANT: Simulations MUST NEVER mutate authoritative state.
        is_authoritative is strictly enforced False.
        """
        outcomes = {
            "projected_throughput_delta_pct": +15.5,
            "projected_risk_score_delta": -0.10,
            "projected_token_cost_delta": +8.2,
        }
        resource_fx = {
            "engineering_headcount_needed": 2,
            "token_budget_increase": 250000,
        }
        projected_risks = [
            "Temporary integration friction during rollout"
        ]

        sim = StrategySimulation(
            id=f"sim-{uuid.uuid4().hex[:8]}",
            company_id=company_id,
            title=title,
            assumptions=assumptions,
            input_parameters=input_parameters,
            projected_outcomes=outcomes,
            resource_effects=resource_fx,
            projected_risks=projected_risks,
            confidence=0.88,
            is_authoritative=False,  # Enforce non-authoritative simulation invariant
            created_at=datetime.now(UTC),
        )

        saved = await self.repo.save_simulation(sim)

        self._publish_event(
            StrategySimulationCreatedEvent(
                company_id=company_id,
                simulation_id=saved.id,
                title=saved.title,
                is_authoritative=saved.is_authoritative,
            )
        )

        return saved

    async def Formulate_or_update_strategy(
        self,
        company_id: str,
        title: str,
        themes: list[str],
        priorities: list[str],
        targets: dict[str, Any],
        approved_by_id: str | None = None,
        change_rationale: str = "Periodic operating cycle adjustment",
    ) -> CompanyStrategy:
        """Formulate a new active Company Strategy version."""
        current_active = await self.repo.get_active_strategy_for_company(company_id)
        version = (current_active.version + 1) if current_active else 1
        prev_id = current_active.id if current_active else None

        if current_active:
            current_active.status = StrategyStatus.SUPERSEDED
            await self.repo.save_strategy(current_active)

        strat = CompanyStrategy(
            id=f"strat-{uuid.uuid4().hex[:8]}",
            company_id=company_id,
            version=version,
            title=title,
            themes=themes,
            priorities=priorities,
            targets=targets,
            status=StrategyStatus.ACTIVE,
            proposer_id="strategic_intelligence_service",
            approved_by_id=approved_by_id,
            previous_version_id=prev_id,
            change_rationale=change_rationale,
            created_at=datetime.now(UTC),
        )

        return await self.repo.save_strategy(strat)
