"""
ExecutiveOrchestrationService for Phase 16 Autonomous Company Operations.

Handles upward department status aggregation, executive strategic reporting,
portfolio management, bottleneck detection, and resource allocation governance.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from src.domain.company import (
    ContinuousImprovementProposal,
    PortfolioItem,
    ResourceAllocationPlan,
)
from src.domain.events import (
    ContinuousImprovementProposalSubmittedEvent,
    DomainEvent,
    ExecutiveReportGeneratedEvent,
    PortfolioItemUpdatedEvent,
    ResourceAllocationPlanApprovedEvent,
)
from src.infrastructure.repositories.company_repository import SQLAlchemyCompanyRepository


class ExecutiveOrchestrationService:
    def __init__(
        self,
        company_repository: SQLAlchemyCompanyRepository,
        department_repository: Any | None = None,
        outbox_publisher: Any | None = None,
    ) -> None:
        self.repo = company_repository
        self.department_repo = department_repository
        self.outbox_publisher = outbox_publisher

    def _publish_event(self, event: DomainEvent) -> None:
        if self.outbox_publisher and hasattr(self.outbox_publisher, "publish"):
            self.outbox_publisher.publish(event)

    async def generate_executive_report(
        self,
        company_id: str,
        cycle_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate comprehensive executive strategic report."""
        company = await self.repo.get_company_by_id(company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        active_strategy = await self.repo.get_active_strategy_for_company(company_id)
        latest_health = await self.repo.get_latest_health_for_company(company_id)
        objectives = await self.repo.list_objectives_for_company(company_id)
        risks = await self.repo.list_risks_for_company(company_id)
        opps = await self.repo.list_opportunities_for_company(company_id)
        portfolio = await self.repo.list_portfolio_items_for_company(company_id)

        report = {
            "report_id": f"report-{uuid.uuid4().hex[:8]}",
            "company_id": company_id,
            "company_name": company.name,
            "code": company.code,
            "cycle_id": cycle_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "active_strategy": {
                "version": active_strategy.version if active_strategy else None,
                "title": active_strategy.title if active_strategy else "Default Strategy",
                "themes": active_strategy.themes if active_strategy else [],
            },
            "health": {
                "overall_status": latest_health.overall_status.value if latest_health else "HEALTHY",
                "operational_health": latest_health.operational_health if latest_health else 1.0,
                "explanation": latest_health.explanation if latest_health else "Normal operations",
            },
            "objectives_count": len(objectives),
            "open_risks_count": len(risks),
            "opportunities_count": len(opps),
            "portfolio_items_count": len(portfolio),
            "bottlenecks": [p.title for p in portfolio if p.has_bottleneck],
        }

        self._publish_event(
            ExecutiveReportGeneratedEvent(
                company_id=company_id,
                report_id=report["report_id"],
                health_status=report["health"]["overall_status"],
                open_risks_count=report["open_risks_count"],
            )
        )

        return report

    async def add_portfolio_item(
        self,
        company_id: str,
        title: str,
        reference_id: str,
        item_type: str = "PROJECT",
        priority: int = 1,
    ) -> PortfolioItem:
        """Register a new item in the company executive portfolio."""
        item = PortfolioItem(
            id=f"port-{uuid.uuid4().hex[:8]}",
            company_id=company_id,
            title=title,
            item_type=item_type,
            reference_id=reference_id,
            priority=priority,
            progress_pct=0.0,
            resource_utilization_pct=0.0,
            status="ACTIVE",
            has_bottleneck=False,
            created_at=datetime.now(UTC),
        )

        saved = await self.repo.save_portfolio_item(item)
        return saved

    async def update_portfolio_progress(
        self,
        item_id: str,
        progress_pct: float,
        resource_utilization_pct: float,
        has_bottleneck: bool = False,
        bottleneck_description: str | None = None,
    ) -> PortfolioItem:
        """Update portfolio item progress and bottleneck state."""
        item = await self.repo.get_portfolio_item_by_id(item_id)
        if not item:
            raise ValueError(f"Portfolio item {item_id} not found")

        item.progress_pct = progress_pct
        item.resource_utilization_pct = resource_utilization_pct
        item.has_bottleneck = has_bottleneck
        item.bottleneck_description = bottleneck_description
        if progress_pct >= 100.0:
            item.status = "COMPLETED"

        saved = await self.repo.save_portfolio_item(item)

        self._publish_event(
            PortfolioItemUpdatedEvent(
                company_id=saved.company_id,
                portfolio_item_id=saved.id,
                progress_pct=saved.progress_pct,
                has_bottleneck=saved.has_bottleneck,
            )
        )

        return saved

    async def create_resource_allocation_plan(
        self,
        company_id: str,
        cycle_id: str | None,
        demand_summary: str,
        allocations: dict[str, Any],
        tradeoffs_summary: str = "",
    ) -> ResourceAllocationPlan:
        """Formulate a resource allocation plan."""
        plan = ResourceAllocationPlan(
            id=f"alloc-{uuid.uuid4().hex[:8]}",
            company_id=company_id,
            cycle_id=cycle_id,
            demand_summary=demand_summary,
            allocations_json=allocations,
            tradeoffs_summary=tradeoffs_summary,
            is_approved=False,
            created_at=datetime.now(UTC),
        )

        return await self.repo.save_allocation_plan(plan)

    async def approve_resource_allocation_plan(
        self,
        plan_id: str,
        approved_by_id: str,
    ) -> ResourceAllocationPlan:
        """Approve a resource allocation plan."""
        plan = await self.repo.get_allocation_plan_by_id(plan_id)
        if not plan:
            raise ValueError(f"Resource allocation plan {plan_id} not found")

        plan.is_approved = True
        plan.approved_by_id = approved_by_id
        saved = await self.repo.save_allocation_plan(plan)

        self._publish_event(
            ResourceAllocationPlanApprovedEvent(
                company_id=saved.company_id,
                plan_id=saved.id,
                approved_by_id=approved_by_id,
            )
        )

        return saved

    async def submit_continuous_improvement_proposal(
        self,
        company_id: str,
        title: str,
        category: str,
        proposed_change: str,
        expected_impact: str,
        governance_required: bool = True,
    ) -> ContinuousImprovementProposal:
        """Submit a continuous improvement proposal from operating cycle retrospective learning."""
        proposal = ContinuousImprovementProposal(
            id=f"imp-{uuid.uuid4().hex[:8]}",
            company_id=company_id,
            title=title,
            category=category,
            proposed_change=proposed_change,
            expected_impact=expected_impact,
            governance_required=governance_required,
            status="PROPOSED",
            created_at=datetime.now(UTC),
        )

        saved = await self.repo.save_improvement_proposal(proposal)

        self._publish_event(
            ContinuousImprovementProposalSubmittedEvent(
                company_id=company_id,
                proposal_id=saved.id,
                title=saved.title,
                governance_required=saved.governance_required,
            )
        )

        return saved
