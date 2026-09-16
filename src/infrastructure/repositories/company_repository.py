"""SQLAlchemy repository implementation for Phase 16 Autonomous Company entities."""

from collections.abc import Sequence

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
        model = res.scalars().first()
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
        model = res.scalars().first()
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
        model = res.scalars().first()
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


# --- Phase 25 Multi-Company & Simulation Repository Implementation ---

import json
from src.domain.company import (
    Company,
    CompanyProfile,
    CompanyMembership,
    CompanyTemplate,
    CompanyRelationship,
    CompanyDataShareRequest,
    CompanyResourceQuota,
    CompanyResourceUsage,
    CompanyLifecycle,
    CompanyType,
    CompanyRole,
    RelationshipType,
    DataShareScope,
    DataShareStatus,
    ExecutionEnvironment,
)
from src.domain.simulation import (
    CompanySimulation,
    SimulationSnapshot,
    SimulationScenario,
    SimulationResult,
    SimulationFinancialRecord,
    SimulationStatus,
)
from src.domain.repository import MultiCompanyRepositoryInterface
from src.infrastructure.models.company_model import (
    CompanyModel,
    CompanyProfileModel,
    CompanyMembershipModel,
    CompanyTemplateModel,
    CompanyRelationshipModel,
    CompanyDataShareRequestModel,
    CompanyResourceQuotaModel,
    CompanyResourceUsageModel,
    CompanySimulationModel,
    SimulationSnapshotModel,
    SimulationScenarioModel,
    SimulationResultModel,
    SimulationFinancialRecordModel,
)


class SQLAlchemyMultiCompanyRepository(MultiCompanyRepositoryInterface):
    """SQLAlchemy persistence repository for Phase 25 Multi-Company & Simulation entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_company(self, company: Company) -> Company:
        model = await self.session.get(CompanyModel, company.id)
        if model is None:
            model = CompanyModel(
                id=company.id,
                name=company.name,
                legal_name=company.legal_name,
                slug=company.slug,
                description=company.description,
                company_type=company.company_type.value,
                industry=company.industry,
                timezone=company.timezone,
                locale=company.locale,
                currency=company.currency,
                lifecycle=company.lifecycle.value,
                owner_id=company.owner_id,
                metadata_json=json.dumps(company.metadata),
                created_at=company.created_at,
                updated_at=company.updated_at,
            )
            self.session.add(model)
        else:
            model.name = company.name
            model.legal_name = company.legal_name
            model.slug = company.slug
            model.description = company.description
            model.company_type = company.company_type.value
            model.industry = company.industry
            model.timezone = company.timezone
            model.locale = company.locale
            model.currency = company.currency
            model.lifecycle = company.lifecycle.value
            model.owner_id = company.owner_id
            model.metadata_json = json.dumps(company.metadata)
            model.updated_at = company.updated_at

        await self.session.flush()
        return Company(
            id=model.id,
            name=model.name,
            legal_name=model.legal_name,
            slug=model.slug,
            description=model.description,
            company_type=CompanyType(model.company_type),
            industry=model.industry,
            timezone=model.timezone,
            locale=model.locale,
            currency=model.currency,
            lifecycle=CompanyLifecycle(model.lifecycle),
            owner_id=model.owner_id,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_company_by_id(self, company_id: str) -> Company | None:
        model = await self.session.get(CompanyModel, company_id)
        if not model:
            return None
        return Company(
            id=model.id,
            name=model.name,
            legal_name=model.legal_name,
            slug=model.slug,
            description=model.description,
            company_type=CompanyType(model.company_type),
            industry=model.industry,
            timezone=model.timezone,
            locale=model.locale,
            currency=model.currency,
            lifecycle=CompanyLifecycle(model.lifecycle),
            owner_id=model.owner_id,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_company_by_slug(self, slug: str) -> Company | None:
        stmt = select(CompanyModel).where(CompanyModel.slug == slug)
        res = await self.session.execute(stmt)
        model = res.scalar_one_or_none()
        if not model:
            return None
        return Company(
            id=model.id,
            name=model.name,
            legal_name=model.legal_name,
            slug=model.slug,
            description=model.description,
            company_type=CompanyType(model.company_type),
            industry=model.industry,
            timezone=model.timezone,
            locale=model.locale,
            currency=model.currency,
            lifecycle=CompanyLifecycle(model.lifecycle),
            owner_id=model.owner_id,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_companies(self) -> list[Company]:
        stmt = select(CompanyModel).order_by(CompanyModel.created_at.desc())
        res = await self.session.execute(stmt)
        models = res.scalars().all()
        return [
            Company(
                id=m.id,
                name=m.name,
                legal_name=m.legal_name,
                slug=m.slug,
                description=m.description,
                company_type=CompanyType(m.company_type),
                industry=m.industry,
                timezone=m.timezone,
                locale=m.locale,
                currency=m.currency,
                lifecycle=CompanyLifecycle(m.lifecycle),
                owner_id=m.owner_id,
                metadata=json.loads(m.metadata_json) if m.metadata_json else {},
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    async def save_company_profile(self, profile: CompanyProfile) -> CompanyProfile:
        model = await self.session.get(CompanyProfileModel, profile.id)
        if not model:
            model = CompanyProfileModel(
                id=profile.id,
                company_id=profile.company_id,
                operating_hours=profile.operating_hours,
                model_routing_policy_json=json.dumps(profile.model_routing_policy),
                tool_policy_json=json.dumps(profile.tool_policy),
                governance_defaults_json=json.dumps(profile.governance_defaults),
                workforce_config_json=json.dumps(profile.workforce_config),
                updated_at=profile.updated_at,
            )
            self.session.add(model)
        else:
            model.operating_hours = profile.operating_hours
            model.model_routing_policy_json = json.dumps(profile.model_routing_policy)
            model.tool_policy_json = json.dumps(profile.tool_policy)
            model.governance_defaults_json = json.dumps(profile.governance_defaults)
            model.workforce_config_json = json.dumps(profile.workforce_config)
            model.updated_at = profile.updated_at

        await self.session.flush()
        return CompanyProfile(
            id=model.id,
            company_id=model.company_id,
            operating_hours=model.operating_hours,
            model_routing_policy=json.loads(model.model_routing_policy_json) if model.model_routing_policy_json else {},
            tool_policy=json.loads(model.tool_policy_json) if model.tool_policy_json else {},
            governance_defaults=json.loads(model.governance_defaults_json) if model.governance_defaults_json else {},
            workforce_config=json.loads(model.workforce_config_json) if model.workforce_config_json else {},
            updated_at=model.updated_at,
        )

    async def get_company_profile(self, company_id: str) -> CompanyProfile | None:
        stmt = select(CompanyProfileModel).where(CompanyProfileModel.company_id == company_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return CompanyProfile(
            id=m.id,
            company_id=m.company_id,
            operating_hours=m.operating_hours,
            model_routing_policy=json.loads(m.model_routing_policy_json) if m.model_routing_policy_json else {},
            tool_policy=json.loads(m.tool_policy_json) if m.tool_policy_json else {},
            governance_defaults=json.loads(m.governance_defaults_json) if m.governance_defaults_json else {},
            workforce_config=json.loads(m.workforce_config_json) if m.workforce_config_json else {},
            updated_at=m.updated_at,
        )

    async def save_membership(self, membership: CompanyMembership) -> CompanyMembership:
        model = await self.session.get(CompanyMembershipModel, membership.id)
        if not model:
            model = CompanyMembershipModel(
                id=membership.id,
                company_id=membership.company_id,
                user_id=membership.user_id,
                role=membership.role.value,
                assigned_at=membership.assigned_at,
            )
            self.session.add(model)
        else:
            model.role = membership.role.value

        await self.session.flush()
        return CompanyMembership(
            id=model.id,
            company_id=model.company_id,
            user_id=model.user_id,
            role=CompanyRole(model.role),
            assigned_at=model.assigned_at,
        )

    async def list_memberships_for_company(self, company_id: str) -> list[CompanyMembership]:
        stmt = select(CompanyMembershipModel).where(CompanyMembershipModel.company_id == company_id)
        res = await self.session.execute(stmt)
        return [
            CompanyMembership(
                id=m.id,
                company_id=m.company_id,
                user_id=m.user_id,
                role=CompanyRole(m.role),
                assigned_at=m.assigned_at,
            )
            for m in res.scalars().all()
        ]

    async def list_memberships_for_user(self, user_id: str) -> list[CompanyMembership]:
        stmt = select(CompanyMembershipModel).where(CompanyMembershipModel.user_id == user_id)
        res = await self.session.execute(stmt)
        return [
            CompanyMembership(
                id=m.id,
                company_id=m.company_id,
                user_id=m.user_id,
                role=CompanyRole(m.role),
                assigned_at=m.assigned_at,
            )
            for m in res.scalars().all()
        ]

    async def save_template(self, template: CompanyTemplate) -> CompanyTemplate:
        model = await self.session.get(CompanyTemplateModel, template.id)
        if not model:
            model = CompanyTemplateModel(
                id=template.id,
                name=template.name,
                description=template.description,
                industry=template.industry,
                structure_json=json.dumps(template.structure_json),
                default_departments_json=json.dumps(template.default_departments),
                default_roles_json=json.dumps(template.default_roles),
                created_at=template.created_at,
            )
            self.session.add(model)
        else:
            model.name = template.name
            model.description = template.description
            model.structure_json = json.dumps(template.structure_json)
            model.default_departments_json = json.dumps(template.default_departments)
            model.default_roles_json = json.dumps(template.default_roles)

        await self.session.flush()
        return CompanyTemplate(
            id=model.id,
            name=model.name,
            description=model.description,
            industry=model.industry,
            structure_json=json.loads(model.structure_json) if model.structure_json else {},
            default_departments=json.loads(model.default_departments_json) if model.default_departments_json else [],
            default_roles=json.loads(model.default_roles_json) if model.default_roles_json else [],
            created_at=model.created_at,
        )

    async def get_template_by_id(self, template_id: str) -> CompanyTemplate | None:
        m = await self.session.get(CompanyTemplateModel, template_id)
        if not m:
            return None
        return CompanyTemplate(
            id=m.id,
            name=m.name,
            description=m.description,
            industry=m.industry,
            structure_json=json.loads(m.structure_json) if m.structure_json else {},
            default_departments=json.loads(m.default_departments_json) if m.default_departments_json else [],
            default_roles=json.loads(m.default_roles_json) if m.default_roles_json else [],
            created_at=m.created_at,
        )

    async def list_templates(self) -> list[CompanyTemplate]:
        stmt = select(CompanyTemplateModel)
        res = await self.session.execute(stmt)
        return [
            CompanyTemplate(
                id=m.id,
                name=m.name,
                description=m.description,
                industry=m.industry,
                structure_json=json.loads(m.structure_json) if m.structure_json else {},
                default_departments=json.loads(m.default_departments_json) if m.default_departments_json else [],
                default_roles=json.loads(m.default_roles_json) if m.default_roles_json else [],
                created_at=m.created_at,
            )
            for m in res.scalars().all()
        ]

    async def save_relationship(self, relationship: CompanyRelationship) -> CompanyRelationship:
        model = await self.session.get(CompanyRelationshipModel, relationship.id)
        if not model:
            model = CompanyRelationshipModel(
                id=relationship.id,
                company_a_id=relationship.company_a_id,
                company_b_id=relationship.company_b_id,
                relationship_type=relationship.relationship_type.value,
                status=relationship.status,
                created_at=relationship.created_at,
            )
            self.session.add(model)
        else:
            model.status = relationship.status

        await self.session.flush()
        return CompanyRelationship(
            id=model.id,
            company_a_id=model.company_a_id,
            company_b_id=model.company_b_id,
            relationship_type=RelationshipType(model.relationship_type),
            status=model.status,
            created_at=model.created_at,
        )

    async def list_relationships_for_company(self, company_id: str) -> list[CompanyRelationship]:
        stmt = select(CompanyRelationshipModel).where(
            (CompanyRelationshipModel.company_a_id == company_id) | (CompanyRelationshipModel.company_b_id == company_id)
        )
        res = await self.session.execute(stmt)
        return [
            CompanyRelationship(
                id=m.id,
                company_a_id=m.company_a_id,
                company_b_id=m.company_b_id,
                relationship_type=RelationshipType(m.relationship_type),
                status=m.status,
                created_at=m.created_at,
            )
            for m in res.scalars().all()
        ]

    async def save_data_share_request(self, request: CompanyDataShareRequest) -> CompanyDataShareRequest:
        model = await self.session.get(CompanyDataShareRequestModel, request.id)
        if not model:
            model = CompanyDataShareRequestModel(
                id=request.id,
                source_company_id=request.source_company_id,
                target_company_id=request.target_company_id,
                data_scope=request.data_scope.value,
                purpose=request.purpose,
                status=request.status.value,
                governance_approval_id=request.governance_approval_id,
                created_at=request.created_at,
                expires_at=request.expires_at,
            )
            self.session.add(model)
        else:
            model.status = request.status.value
            model.governance_approval_id = request.governance_approval_id

        await self.session.flush()
        return CompanyDataShareRequest(
            id=model.id,
            source_company_id=model.source_company_id,
            target_company_id=model.target_company_id,
            data_scope=DataShareScope(model.data_scope),
            purpose=model.purpose,
            status=DataShareStatus(model.status),
            governance_approval_id=model.governance_approval_id,
            created_at=model.created_at,
            expires_at=model.expires_at,
        )

    async def get_data_share_request_by_id(self, request_id: str) -> CompanyDataShareRequest | None:
        m = await self.session.get(CompanyDataShareRequestModel, request_id)
        if not m:
            return None
        return CompanyDataShareRequest(
            id=m.id,
            source_company_id=m.source_company_id,
            target_company_id=m.target_company_id,
            data_scope=DataShareScope(m.data_scope),
            purpose=m.purpose,
            status=DataShareStatus(m.status),
            governance_approval_id=m.governance_approval_id,
            created_at=m.created_at,
            expires_at=m.expires_at,
        )

    async def list_data_share_requests_for_company(self, company_id: str) -> list[CompanyDataShareRequest]:
        stmt = select(CompanyDataShareRequestModel).where(
            (CompanyDataShareRequestModel.source_company_id == company_id) | (CompanyDataShareRequestModel.target_company_id == company_id)
        )
        res = await self.session.execute(stmt)
        return [
            CompanyDataShareRequest(
                id=m.id,
                source_company_id=m.source_company_id,
                target_company_id=m.target_company_id,
                data_scope=DataShareScope(m.data_scope),
                purpose=m.purpose,
                status=DataShareStatus(m.status),
                governance_approval_id=m.governance_approval_id,
                created_at=m.created_at,
                expires_at=m.expires_at,
            )
            for m in res.scalars().all()
        ]

    async def save_resource_quota(self, quota: CompanyResourceQuota) -> CompanyResourceQuota:
        model = await self.session.get(CompanyResourceQuotaModel, quota.id)
        if not model:
            model = CompanyResourceQuotaModel(
                id=quota.id,
                company_id=quota.company_id,
                max_concurrent_tasks=quota.max_concurrent_tasks,
                max_concurrent_agents=quota.max_concurrent_agents,
                max_monthly_model_calls=quota.max_monthly_model_calls,
                max_storage_mb=quota.max_storage_mb,
                max_simulations=quota.max_simulations,
                updated_at=quota.updated_at,
            )
            self.session.add(model)
        else:
            model.max_concurrent_tasks = quota.max_concurrent_tasks
            model.max_concurrent_agents = quota.max_concurrent_agents
            model.max_monthly_model_calls = quota.max_monthly_model_calls
            model.max_storage_mb = quota.max_storage_mb
            model.max_simulations = quota.max_simulations
            model.updated_at = quota.updated_at

        await self.session.flush()
        return CompanyResourceQuota(
            id=model.id,
            company_id=model.company_id,
            max_concurrent_tasks=model.max_concurrent_tasks,
            max_concurrent_agents=model.max_concurrent_agents,
            max_monthly_model_calls=model.max_monthly_model_calls,
            max_storage_mb=model.max_storage_mb,
            max_simulations=model.max_simulations,
            updated_at=model.updated_at,
        )

    async def get_resource_quota_by_company_id(self, company_id: str) -> CompanyResourceQuota | None:
        stmt = select(CompanyResourceQuotaModel).where(CompanyResourceQuotaModel.company_id == company_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return CompanyResourceQuota(
            id=m.id,
            company_id=m.company_id,
            max_concurrent_tasks=m.max_concurrent_tasks,
            max_concurrent_agents=m.max_concurrent_agents,
            max_monthly_model_calls=m.max_monthly_model_calls,
            max_storage_mb=m.max_storage_mb,
            max_simulations=m.max_simulations,
            updated_at=m.updated_at,
        )

    async def save_resource_usage(self, usage: CompanyResourceUsage) -> CompanyResourceUsage:
        model = await self.session.get(CompanyResourceUsageModel, usage.id)
        if not model:
            model = CompanyResourceUsageModel(
                id=usage.id,
                company_id=usage.company_id,
                active_tasks=usage.active_tasks,
                active_agents=usage.active_agents,
                monthly_model_calls=usage.monthly_model_calls,
                storage_mb=usage.storage_mb,
                active_simulations=usage.active_simulations,
                recorded_at=usage.recorded_at,
            )
            self.session.add(model)
        else:
            model.active_tasks = usage.active_tasks
            model.active_agents = usage.active_agents
            model.monthly_model_calls = usage.monthly_model_calls
            model.storage_mb = usage.storage_mb
            model.active_simulations = usage.active_simulations
            model.recorded_at = usage.recorded_at

        await self.session.flush()
        return CompanyResourceUsage(
            id=model.id,
            company_id=model.company_id,
            active_tasks=model.active_tasks,
            active_agents=model.active_agents,
            monthly_model_calls=model.monthly_model_calls,
            storage_mb=model.storage_mb,
            active_simulations=model.active_simulations,
            recorded_at=model.recorded_at,
        )

    async def get_resource_usage_by_company_id(self, company_id: str) -> CompanyResourceUsage | None:
        stmt = select(CompanyResourceUsageModel).where(CompanyResourceUsageModel.company_id == company_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return CompanyResourceUsage(
            id=m.id,
            company_id=m.company_id,
            active_tasks=m.active_tasks,
            active_agents=m.active_agents,
            monthly_model_calls=m.monthly_model_calls,
            storage_mb=m.storage_mb,
            active_simulations=m.active_simulations,
            recorded_at=m.recorded_at,
        )

    async def save_simulation(self, simulation: CompanySimulation) -> CompanySimulation:
        model = await self.session.get(CompanySimulationModel, simulation.id)
        if not model:
            model = CompanySimulationModel(
                id=simulation.id,
                company_id=simulation.company_id,
                name=simulation.name,
                scenario_id=simulation.scenario_id,
                snapshot_id=simulation.snapshot_id,
                environment=simulation.environment.value,
                status=simulation.status.value,
                owner_id=simulation.owner_id,
                metadata_json=json.dumps(simulation.metadata),
                created_at=simulation.created_at,
                updated_at=simulation.updated_at,
            )
            self.session.add(model)
        else:
            model.status = simulation.status.value
            model.metadata_json = json.dumps(simulation.metadata)
            model.updated_at = simulation.updated_at

        await self.session.flush()
        return CompanySimulation(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            scenario_id=model.scenario_id,
            snapshot_id=model.snapshot_id,
            environment=ExecutionEnvironment(model.environment),
            status=SimulationStatus(model.status),
            owner_id=model.owner_id,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_simulation_by_id(self, simulation_id: str) -> CompanySimulation | None:
        m = await self.session.get(CompanySimulationModel, simulation_id)
        if not m:
            return None
        return CompanySimulation(
            id=m.id,
            company_id=m.company_id,
            name=m.name,
            scenario_id=m.scenario_id,
            snapshot_id=m.snapshot_id,
            environment=ExecutionEnvironment(m.environment),
            status=SimulationStatus(m.status),
            owner_id=m.owner_id,
            metadata=json.loads(m.metadata_json) if m.metadata_json else {},
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    async def list_simulations_for_company(self, company_id: str) -> list[CompanySimulation]:
        stmt = select(CompanySimulationModel).where(CompanySimulationModel.company_id == company_id)
        res = await self.session.execute(stmt)
        return [
            CompanySimulation(
                id=m.id,
                company_id=m.company_id,
                name=m.name,
                scenario_id=m.scenario_id,
                snapshot_id=m.snapshot_id,
                environment=ExecutionEnvironment(m.environment),
                status=SimulationStatus(m.status),
                owner_id=m.owner_id,
                metadata=json.loads(m.metadata_json) if m.metadata_json else {},
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in res.scalars().all()
        ]

    async def save_simulation_snapshot(self, snapshot: SimulationSnapshot) -> SimulationSnapshot:
        model = await self.session.get(SimulationSnapshotModel, snapshot.id)
        if not model:
            model = SimulationSnapshotModel(
                id=snapshot.id,
                company_id=snapshot.company_id,
                snapshot_name=snapshot.snapshot_name,
                snapshot_data_json=json.dumps(snapshot.snapshot_data),
                recorded_at=snapshot.recorded_at,
            )
            self.session.add(model)
        else:
            model.snapshot_data_json = json.dumps(snapshot.snapshot_data)

        await self.session.flush()
        return SimulationSnapshot(
            id=model.id,
            company_id=model.company_id,
            snapshot_name=model.snapshot_name,
            snapshot_data=json.loads(model.snapshot_data_json) if model.snapshot_data_json else {},
            recorded_at=model.recorded_at,
        )

    async def get_simulation_snapshot_by_id(self, snapshot_id: str) -> SimulationSnapshot | None:
        m = await self.session.get(SimulationSnapshotModel, snapshot_id)
        if not m:
            return None
        return SimulationSnapshot(
            id=m.id,
            company_id=m.company_id,
            snapshot_name=m.snapshot_name,
            snapshot_data=json.loads(m.snapshot_data_json) if m.snapshot_data_json else {},
            recorded_at=m.recorded_at,
        )

    async def save_simulation_scenario(self, scenario: SimulationScenario) -> SimulationScenario:
        model = await self.session.get(SimulationScenarioModel, scenario.id)
        if not model:
            model = SimulationScenarioModel(
                id=scenario.id,
                company_id=scenario.company_id,
                name=scenario.name,
                description=scenario.description,
                variables_json=json.dumps(scenario.variables),
                created_at=scenario.created_at,
            )
            self.session.add(model)
        else:
            model.name = scenario.name
            model.variables_json = json.dumps(scenario.variables)

        await self.session.flush()
        return SimulationScenario(
            id=model.id,
            company_id=model.company_id,
            name=model.name,
            description=model.description,
            variables=json.loads(model.variables_json) if model.variables_json else {},
            created_at=model.created_at,
        )

    async def get_simulation_scenario_by_id(self, scenario_id: str) -> SimulationScenario | None:
        m = await self.session.get(SimulationScenarioModel, scenario_id)
        if not m:
            return None
        return SimulationScenario(
            id=m.id,
            company_id=m.company_id,
            name=m.name,
            description=m.description,
            variables=json.loads(m.variables_json) if m.variables_json else {},
            created_at=m.created_at,
        )

    async def save_simulation_result(self, result: SimulationResult) -> SimulationResult:
        model = await self.session.get(SimulationResultModel, result.id)
        if not model:
            model = SimulationResultModel(
                id=result.id,
                simulation_id=result.simulation_id,
                company_id=result.company_id,
                scenario_name=result.scenario_name,
                baseline_metrics_json=json.dumps(result.baseline_metrics),
                simulated_metrics_json=json.dumps(result.simulated_metrics),
                variance_analysis_json=json.dumps(result.variance_analysis),
                confidence_score=result.confidence_score,
                produced_at=result.produced_at,
            )
            self.session.add(model)
        else:
            model.simulated_metrics_json = json.dumps(result.simulated_metrics)
            model.variance_analysis_json = json.dumps(result.variance_analysis)

        await self.session.flush()
        return SimulationResult(
            id=model.id,
            simulation_id=model.simulation_id,
            company_id=model.company_id,
            scenario_name=model.scenario_name,
            baseline_metrics=json.loads(model.baseline_metrics_json) if model.baseline_metrics_json else {},
            simulated_metrics=json.loads(model.simulated_metrics_json) if model.simulated_metrics_json else {},
            variance_analysis=json.loads(model.variance_analysis_json) if model.variance_analysis_json else {},
            confidence_score=model.confidence_score,
            produced_at=model.produced_at,
        )

    async def get_simulation_result_by_simulation_id(self, simulation_id: str) -> SimulationResult | None:
        stmt = select(SimulationResultModel).where(SimulationResultModel.simulation_id == simulation_id)
        res = await self.session.execute(stmt)
        m = res.scalar_one_or_none()
        if not m:
            return None
        return SimulationResult(
            id=m.id,
            simulation_id=m.simulation_id,
            company_id=m.company_id,
            scenario_name=m.scenario_name,
            baseline_metrics=json.loads(m.baseline_metrics_json) if m.baseline_metrics_json else {},
            simulated_metrics=json.loads(m.simulated_metrics_json) if m.simulated_metrics_json else {},
            variance_analysis=json.loads(m.variance_analysis_json) if m.variance_analysis_json else {},
            confidence_score=m.confidence_score,
            produced_at=m.produced_at,
        )

    async def save_simulation_financial_record(self, record: SimulationFinancialRecord) -> SimulationFinancialRecord:
        model = await self.session.get(SimulationFinancialRecordModel, record.id)
        if not model:
            model = SimulationFinancialRecordModel(
                id=record.id,
                simulation_id=record.simulation_id,
                company_id=record.company_id,
                record_type=record.record_type,
                amount_cents=record.amount_cents,
                currency=record.currency,
                description=record.description,
                created_at=record.created_at,
            )
            self.session.add(model)

        await self.session.flush()
        return SimulationFinancialRecord(
            id=model.id,
            simulation_id=model.simulation_id,
            company_id=model.company_id,
            record_type=model.record_type,
            amount_cents=model.amount_cents,
            currency=model.currency,
            description=model.description,
            created_at=model.created_at,
        )

    async def list_simulation_financial_records(self, simulation_id: str) -> list[SimulationFinancialRecord]:
        stmt = select(SimulationFinancialRecordModel).where(SimulationFinancialRecordModel.simulation_id == simulation_id)
        res = await self.session.execute(stmt)
        return [
            SimulationFinancialRecord(
                id=m.id,
                simulation_id=m.simulation_id,
                company_id=m.company_id,
                record_type=m.record_type,
                amount_cents=m.amount_cents,
                currency=m.currency,
                description=m.description,
                created_at=m.created_at,
            )
            for m in res.scalars().all()
        ]

