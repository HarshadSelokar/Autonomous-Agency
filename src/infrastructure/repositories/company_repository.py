"""SQLAlchemy repository implementation for Phase 16 Autonomous Company entities."""

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.company import (
    AutonomousCompany,
    CompanyHealthSnapshot,
    CompanyKPISnapshot,
    CompanyOperatingCycle,
    CompanyOpportunity,
    CompanyRisk,
    ContinuousImprovementProposal,
    PortfolioItem,
    ResourceAllocationPlan,
)
from src.domain.strategy import (
    CompanyStrategy,
    StrategicAnalysis,
    StrategicInitiative,
    StrategicObjective,
    StrategyProposal,
    StrategySimulation,
)
from src.infrastructure.models.company_model import (
    AutonomousCompanyModel,
    CompanyHealthSnapshotModel,
    CompanyMetricSnapshotModel,
    CompanyOperatingCycleModel,
    CompanyOpportunityModel,
    CompanyRiskModel,
    CompanyStrategyModel,
    ContinuousImprovementProposalModel,
    PortfolioItemModel,
    ResourceAllocationPlanModel,
    StrategicAnalysisModel,
    StrategicInitiativeModel,
    StrategicObjectiveModel,
    StrategyProposalModel,
    StrategySimulationModel,
)


class SQLAlchemyCompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------------------------------------------------------
    # Autonomous Company
    # ---------------------------------------------------------
    async def save_company(self, company: AutonomousCompany) -> AutonomousCompany:
        model = await self.session.get(AutonomousCompanyModel, company.id)
        if model is None:
            model = AutonomousCompanyModel.from_domain(company)
            self.session.add(model)
        else:
            updated = AutonomousCompanyModel.from_domain(company)
            model.name = updated.name
            model.code = updated.code
            model.mission = updated.mission
            model.status = updated.status
            model.settings_json = updated.settings_json
            model.updated_at = updated.updated_at
        await self.session.flush()
        return model.to_domain()

    async def get_company_by_id(self, company_id: str) -> AutonomousCompany | None:
        model = await self.session.get(AutonomousCompanyModel, company_id)
        return model.to_domain() if model else None

    async def get_company_by_code(self, code: str) -> AutonomousCompany | None:
        stmt = select(AutonomousCompanyModel).where(AutonomousCompanyModel.code == code)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_domain() if model else None

    # ---------------------------------------------------------
    # Operating Cycle
    # ---------------------------------------------------------
    async def save_cycle(self, cycle: CompanyOperatingCycle) -> CompanyOperatingCycle:
        model = await self.session.get(CompanyOperatingCycleModel, cycle.id)
        if model is None:
            model = CompanyOperatingCycleModel.from_domain(cycle)
            self.session.add(model)
        else:
            updated = CompanyOperatingCycleModel.from_domain(cycle)
            model.cycle_number = updated.cycle_number
            model.state = updated.state
            model.checkpoint_data_json = updated.checkpoint_data_json
            model.initiated_by_id = updated.initiated_by_id
            model.completed_at = updated.completed_at
            model.failure_reason = updated.failure_reason
        await self.session.flush()
        return model.to_domain()

    async def get_cycle_by_id(self, cycle_id: str) -> CompanyOperatingCycle | None:
        model = await self.session.get(CompanyOperatingCycleModel, cycle_id)
        return model.to_domain() if model else None

    async def get_active_cycle_for_company(self, company_id: str) -> CompanyOperatingCycle | None:
        stmt = (
            select(CompanyOperatingCycleModel)
            .where(
                CompanyOperatingCycleModel.company_id == company_id,
                CompanyOperatingCycleModel.state.notin_(["COMPLETED", "FAILED", "CANCELLED"]),
            )
            .order_by(CompanyOperatingCycleModel.cycle_number.desc())
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_cycles_for_company(self, company_id: str) -> Sequence[CompanyOperatingCycle]:
        stmt = (
            select(CompanyOperatingCycleModel)
            .where(CompanyOperatingCycleModel.company_id == company_id)
            .order_by(CompanyOperatingCycleModel.cycle_number.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Strategy
    # ---------------------------------------------------------
    async def save_strategy(self, strategy: CompanyStrategy) -> CompanyStrategy:
        model = await self.session.get(CompanyStrategyModel, strategy.id)
        if model is None:
            model = CompanyStrategyModel.from_domain(strategy)
            self.session.add(model)
        else:
            updated = CompanyStrategyModel.from_domain(strategy)
            model.version = updated.version
            model.title = updated.title
            model.themes_json = updated.themes_json
            model.constraints_json = updated.constraints_json
            model.priorities_json = updated.priorities_json
            model.targets_json = updated.targets_json
            model.assumptions_json = updated.assumptions_json
            model.status = updated.status
            model.approved_by_id = updated.approved_by_id
            model.change_rationale = updated.change_rationale
        await self.session.flush()
        return model.to_domain()

    async def get_strategy_by_id(self, strategy_id: str) -> CompanyStrategy | None:
        model = await self.session.get(CompanyStrategyModel, strategy_id)
        return model.to_domain() if model else None

    async def get_active_strategy_for_company(self, company_id: str) -> CompanyStrategy | None:
        stmt = (
            select(CompanyStrategyModel)
            .where(
                CompanyStrategyModel.company_id == company_id,
                CompanyStrategyModel.status == "ACTIVE",
            )
            .order_by(CompanyStrategyModel.version.desc())
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_strategies_for_company(self, company_id: str) -> Sequence[CompanyStrategy]:
        stmt = (
            select(CompanyStrategyModel)
            .where(CompanyStrategyModel.company_id == company_id)
            .order_by(CompanyStrategyModel.version.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Objectives & Initiatives
    # ---------------------------------------------------------
    async def save_objective(self, objective: StrategicObjective) -> StrategicObjective:
        model = await self.session.get(StrategicObjectiveModel, objective.id)
        if model is None:
            model = StrategicObjectiveModel.from_domain(objective)
            self.session.add(model)
        else:
            updated = StrategicObjectiveModel.from_domain(objective)
            model.title = updated.title
            model.description = updated.description
            model.target_metric = updated.target_metric
            model.target_value = updated.target_value
            model.current_value = updated.current_value
            model.priority = updated.priority
            model.status = updated.status
        await self.session.flush()
        return model.to_domain()

    async def get_objective_by_id(self, objective_id: str) -> StrategicObjective | None:
        model = await self.session.get(StrategicObjectiveModel, objective_id)
        return model.to_domain() if model else None

    async def list_objectives_for_company(self, company_id: str) -> Sequence[StrategicObjective]:
        stmt = (
            select(StrategicObjectiveModel)
            .where(StrategicObjectiveModel.company_id == company_id)
            .order_by(StrategicObjectiveModel.priority.asc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_initiative(self, initiative: StrategicInitiative) -> StrategicInitiative:
        model = await self.session.get(StrategicInitiativeModel, initiative.id)
        if model is None:
            model = StrategicInitiativeModel.from_domain(initiative)
            self.session.add(model)
        else:
            updated = StrategicInitiativeModel.from_domain(initiative)
            model.title = updated.title
            model.description = updated.description
            model.lead_department_id = updated.lead_department_id
            model.project_ids_json = updated.project_ids_json
            model.status = updated.status
            model.budget_tokens = updated.budget_tokens
            model.spent_tokens = updated.spent_tokens
        await self.session.flush()
        return model.to_domain()

    async def get_initiative_by_id(self, initiative_id: str) -> StrategicInitiative | None:
        model = await self.session.get(StrategicInitiativeModel, initiative_id)
        return model.to_domain() if model else None

    async def list_initiatives_for_objective(self, objective_id: str) -> Sequence[StrategicInitiative]:
        stmt = select(StrategicInitiativeModel).where(
            StrategicInitiativeModel.strategic_objective_id == objective_id
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Metrics & Health Snapshots
    # ---------------------------------------------------------
    async def save_metric_snapshot(self, snapshot: CompanyKPISnapshot) -> CompanyKPISnapshot:
        model = await self.session.get(CompanyMetricSnapshotModel, snapshot.id)
        if model is None:
            model = CompanyMetricSnapshotModel.from_domain(snapshot)
            self.session.add(model)
        else:
            updated = CompanyMetricSnapshotModel.from_domain(snapshot)
            model.value = updated.value
            model.target_value = updated.target_value
            model.trend = updated.trend
            model.confidence = updated.confidence
            model.freshness_seconds = updated.freshness_seconds
            model.provenance_sources_json = updated.provenance_sources_json
        await self.session.flush()
        return model.to_domain()

    async def list_metric_snapshots_for_company(self, company_id: str) -> Sequence[CompanyKPISnapshot]:
        stmt = (
            select(CompanyMetricSnapshotModel)
            .where(CompanyMetricSnapshotModel.company_id == company_id)
            .order_by(CompanyMetricSnapshotModel.timestamp.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_health_snapshot(self, snapshot: CompanyHealthSnapshot) -> CompanyHealthSnapshot:
        model = await self.session.get(CompanyHealthSnapshotModel, snapshot.id)
        if model is None:
            model = CompanyHealthSnapshotModel.from_domain(snapshot)
            self.session.add(model)
        else:
            updated = CompanyHealthSnapshotModel.from_domain(snapshot)
            model.operational_health = updated.operational_health
            model.execution_health = updated.execution_health
            model.delivery_health = updated.delivery_health
            model.quality_health = updated.quality_health
            model.workforce_health = updated.workforce_health
            model.reliability_health = updated.reliability_health
            model.resource_health = updated.resource_health
            model.governance_health = updated.governance_health
            model.security_health = updated.security_health
            model.overall_status = updated.overall_status
            model.explanation = updated.explanation
        await self.session.flush()
        return model.to_domain()

    async def get_latest_health_for_company(self, company_id: str) -> CompanyHealthSnapshot | None:
        stmt = (
            select(CompanyHealthSnapshotModel)
            .where(CompanyHealthSnapshotModel.company_id == company_id)
            .order_by(CompanyHealthSnapshotModel.evaluated_at.desc())
        )
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        return model.to_domain() if model else None

    # ---------------------------------------------------------
    # Risks & Opportunities
    # ---------------------------------------------------------
    async def save_risk(self, risk: CompanyRisk) -> CompanyRisk:
        model = await self.session.get(CompanyRiskModel, risk.id)
        if model is None:
            model = CompanyRiskModel.from_domain(risk)
            self.session.add(model)
        else:
            updated = CompanyRiskModel.from_domain(risk)
            model.probability = updated.probability
            model.impact = updated.impact
            model.severity = updated.severity
            model.mitigation_plan = updated.mitigation_plan
            model.status = updated.status
        await self.session.flush()
        return model.to_domain()

    async def get_risk_by_id(self, risk_id: str) -> CompanyRisk | None:
        model = await self.session.get(CompanyRiskModel, risk_id)
        return model.to_domain() if model else None

    async def list_risks_for_company(self, company_id: str) -> Sequence[CompanyRisk]:
        stmt = (
            select(CompanyRiskModel)
            .where(CompanyRiskModel.company_id == company_id)
            .order_by(CompanyRiskModel.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_opportunity(self, opportunity: CompanyOpportunity) -> CompanyOpportunity:
        model = await self.session.get(CompanyOpportunityModel, opportunity.id)
        if model is None:
            model = CompanyOpportunityModel.from_domain(opportunity)
            self.session.add(model)
        else:
            updated = CompanyOpportunityModel.from_domain(opportunity)
            model.expected_value = updated.expected_value
            model.confidence = updated.confidence
            model.status = updated.status
        await self.session.flush()
        return model.to_domain()

    async def get_opportunity_by_id(self, opportunity_id: str) -> CompanyOpportunity | None:
        model = await self.session.get(CompanyOpportunityModel, opportunity_id)
        return model.to_domain() if model else None

    async def list_opportunities_for_company(self, company_id: str) -> Sequence[CompanyOpportunity]:
        stmt = (
            select(CompanyOpportunityModel)
            .where(CompanyOpportunityModel.company_id == company_id)
            .order_by(CompanyOpportunityModel.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Analysis & Proposals
    # ---------------------------------------------------------
    async def save_analysis(self, analysis: StrategicAnalysis) -> StrategicAnalysis:
        model = await self.session.get(StrategicAnalysisModel, analysis.id)
        if model is None:
            model = StrategicAnalysisModel.from_domain(analysis)
            self.session.add(model)
        else:
            updated = StrategicAnalysisModel.from_domain(analysis)
            model.current_situation = updated.current_situation
            model.observed_facts_json = updated.observed_facts_json
            model.trends_json = updated.trends_json
            model.risks_json = updated.risks_json
            model.opportunities_json = updated.opportunities_json
            model.constraints_json = updated.constraints_json
            model.confidence = updated.confidence
        await self.session.flush()
        return model.to_domain()

    async def get_analysis_by_id(self, analysis_id: str) -> StrategicAnalysis | None:
        model = await self.session.get(StrategicAnalysisModel, analysis_id)
        return model.to_domain() if model else None

    async def list_analyses_for_company(self, company_id: str) -> Sequence[StrategicAnalysis]:
        stmt = (
            select(StrategicAnalysisModel)
            .where(StrategicAnalysisModel.company_id == company_id)
            .order_by(StrategicAnalysisModel.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_proposal(self, proposal: StrategyProposal) -> StrategyProposal:
        model = await self.session.get(StrategyProposalModel, proposal.id)
        if model is None:
            model = StrategyProposalModel.from_domain(proposal)
            self.session.add(model)
        else:
            updated = StrategyProposalModel.from_domain(proposal)
            model.status = updated.status
            model.governance_approval_id = updated.governance_approval_id
            model.processed_at = updated.processed_at
        await self.session.flush()
        return model.to_domain()

    async def get_proposal_by_id(self, proposal_id: str) -> StrategyProposal | None:
        model = await self.session.get(StrategyProposalModel, proposal_id)
        return model.to_domain() if model else None

    async def list_proposals_for_company(self, company_id: str) -> Sequence[StrategyProposal]:
        stmt = (
            select(StrategyProposalModel)
            .where(StrategyProposalModel.company_id == company_id)
            .order_by(StrategyProposalModel.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Portfolio, Allocations & Improvements
    # ---------------------------------------------------------
    async def save_portfolio_item(self, item: PortfolioItem) -> PortfolioItem:
        model = await self.session.get(PortfolioItemModel, item.id)
        if model is None:
            model = PortfolioItemModel.from_domain(item)
            self.session.add(model)
        else:
            updated = PortfolioItemModel.from_domain(item)
            model.priority = updated.priority
            model.progress_pct = updated.progress_pct
            model.resource_utilization_pct = updated.resource_utilization_pct
            model.status = updated.status
            model.has_bottleneck = updated.has_bottleneck
            model.bottleneck_description = updated.bottleneck_description
        await self.session.flush()
        return model.to_domain()

    async def get_portfolio_item_by_id(self, item_id: str) -> PortfolioItem | None:
        model = await self.session.get(PortfolioItemModel, item_id)
        return model.to_domain() if model else None

    async def list_portfolio_items_for_company(self, company_id: str) -> Sequence[PortfolioItem]:
        stmt = (
            select(PortfolioItemModel)
            .where(PortfolioItemModel.company_id == company_id)
            .order_by(PortfolioItemModel.priority.asc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_allocation_plan(self, plan: ResourceAllocationPlan) -> ResourceAllocationPlan:
        model = await self.session.get(ResourceAllocationPlanModel, plan.id)
        if model is None:
            model = ResourceAllocationPlanModel.from_domain(plan)
            self.session.add(model)
        else:
            updated = ResourceAllocationPlanModel.from_domain(plan)
            model.demand_summary = updated.demand_summary
            model.allocations_json = updated.allocations_json
            model.tradeoffs_summary = updated.tradeoffs_summary
            model.is_approved = updated.is_approved
            model.approved_by_id = updated.approved_by_id
        await self.session.flush()
        return model.to_domain()

    async def get_allocation_plan_by_id(self, plan_id: str) -> ResourceAllocationPlan | None:
        model = await self.session.get(ResourceAllocationPlanModel, plan_id)
        return model.to_domain() if model else None

    async def list_allocation_plans_for_company(self, company_id: str) -> Sequence[ResourceAllocationPlan]:
        stmt = (
            select(ResourceAllocationPlanModel)
            .where(ResourceAllocationPlanModel.company_id == company_id)
            .order_by(ResourceAllocationPlanModel.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    async def save_improvement_proposal(self, proposal: ContinuousImprovementProposal) -> ContinuousImprovementProposal:
        model = await self.session.get(ContinuousImprovementProposalModel, proposal.id)
        if model is None:
            model = ContinuousImprovementProposalModel.from_domain(proposal)
            self.session.add(model)
        else:
            updated = ContinuousImprovementProposalModel.from_domain(proposal)
            model.status = updated.status
        await self.session.flush()
        return model.to_domain()

    async def get_improvement_proposal_by_id(self, proposal_id: str) -> ContinuousImprovementProposal | None:
        model = await self.session.get(ContinuousImprovementProposalModel, proposal_id)
        return model.to_domain() if model else None

    async def list_improvement_proposals_for_company(self, company_id: str) -> Sequence[ContinuousImprovementProposal]:
        stmt = (
            select(ContinuousImprovementProposalModel)
            .where(ContinuousImprovementProposalModel.company_id == company_id)
            .order_by(ContinuousImprovementProposalModel.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]

    # ---------------------------------------------------------
    # Simulations
    # ---------------------------------------------------------
    async def save_simulation(self, simulation: StrategySimulation) -> StrategySimulation:
        model = await self.session.get(StrategySimulationModel, simulation.id)
        if model is None:
            model = StrategySimulationModel.from_domain(simulation)
            self.session.add(model)
        else:
            updated = StrategySimulationModel.from_domain(simulation)
            model.projected_outcomes_json = updated.projected_outcomes_json
            model.resource_effects_json = updated.resource_effects_json
            model.projected_risks_json = updated.projected_risks_json
            model.confidence = updated.confidence
        await self.session.flush()
        return model.to_domain()

    async def get_simulation_by_id(self, simulation_id: str) -> StrategySimulation | None:
        model = await self.session.get(StrategySimulationModel, simulation_id)
        return model.to_domain() if model else None

    async def list_simulations_for_company(self, company_id: str) -> Sequence[StrategySimulation]:
        stmt = (
            select(StrategySimulationModel)
            .where(StrategySimulationModel.company_id == company_id)
            .order_by(StrategySimulationModel.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return [m.to_domain() for m in res.scalars().all()]
