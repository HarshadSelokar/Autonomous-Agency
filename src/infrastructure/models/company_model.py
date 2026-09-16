"""SQLAlchemy ORM Models for Autonomous Company, Strategies, Metrics, Health, Risks, Proposals, and Simulations."""

import json
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.company import (
    AutonomousCompany,
    CompanyHealthSnapshot,
    CompanyHealthStatus,
    CompanyKPISnapshot,
    CompanyOperatingCycle,
    CompanyOpportunity,
    CompanyRisk,
    CompanyStatus,
    ContinuousImprovementProposal,
    MetricTrend,
    OperatingCycleState,
    PortfolioItem,
    ResourceAllocationPlan,
    RiskSeverity,
)
from src.domain.strategy import (
    CompanyStrategy,
    StrategicAnalysis,
    StrategicInitiative,
    StrategicObjective,
    StrategyProposal,
    StrategyProposalStatus,
    StrategyProposalType,
    StrategySimulation,
    StrategyStatus,
)
from src.infrastructure.database import Base


class AutonomousCompanyModel(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    mission: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    settings_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> AutonomousCompany:
        return AutonomousCompany(
            id=self.id,
            name=self.name,
            code=self.code,
            mission=self.mission,
            status=CompanyStatus(self.status),
            settings=json.loads(self.settings_json) if self.settings_json else {},
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: AutonomousCompany) -> "AutonomousCompanyModel":
        return cls(
            id=entity.id,
            name=entity.name,
            code=entity.code,
            mission=entity.mission,
            status=entity.status.value if isinstance(entity.status, Enum) else str(entity.status),
            settings_json=json.dumps(entity.settings),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class CompanyOperatingCycleModel(Base):
    __tablename__ = "company_operating_cycles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="CREATED")
    checkpoint_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    initiated_by_id: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_domain(self) -> CompanyOperatingCycle:
        return CompanyOperatingCycle(
            id=self.id,
            company_id=self.company_id,
            cycle_number=self.cycle_number,
            state=OperatingCycleState(self.state),
            checkpoint_data=json.loads(self.checkpoint_data_json) if self.checkpoint_data_json else {},
            initiated_by_id=self.initiated_by_id,
            started_at=self.started_at,
            completed_at=self.completed_at,
            failure_reason=self.failure_reason,
        )

    @classmethod
    def from_domain(cls, entity: CompanyOperatingCycle) -> "CompanyOperatingCycleModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            cycle_number=entity.cycle_number,
            state=entity.state.value if isinstance(entity.state, Enum) else str(entity.state),
            checkpoint_data_json=json.dumps(entity.checkpoint_data),
            initiated_by_id=entity.initiated_by_id,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            failure_reason=entity.failure_reason,
        )


class CompanyStrategyModel(Base):
    __tablename__ = "company_strategies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    themes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    constraints_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    priorities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    targets_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    assumptions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    proposer_id: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    approved_by_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    previous_version_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    change_rationale: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> CompanyStrategy:
        return CompanyStrategy(
            id=self.id,
            company_id=self.company_id,
            version=self.version,
            title=self.title,
            themes=json.loads(self.themes_json) if self.themes_json else [],
            constraints=json.loads(self.constraints_json) if self.constraints_json else [],
            priorities=json.loads(self.priorities_json) if self.priorities_json else [],
            targets=json.loads(self.targets_json) if self.targets_json else {},
            assumptions=json.loads(self.assumptions_json) if self.assumptions_json else [],
            status=StrategyStatus(self.status),
            proposer_id=self.proposer_id,
            approved_by_id=self.approved_by_id,
            previous_version_id=self.previous_version_id,
            change_rationale=self.change_rationale,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: CompanyStrategy) -> "CompanyStrategyModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            version=entity.version,
            title=entity.title,
            themes_json=json.dumps(entity.themes),
            constraints_json=json.dumps(entity.constraints),
            priorities_json=json.dumps(entity.priorities),
            targets_json=json.dumps(entity.targets),
            assumptions_json=json.dumps(entity.assumptions),
            status=entity.status.value if isinstance(entity.status, Enum) else str(entity.status),
            proposer_id=entity.proposer_id,
            approved_by_id=entity.approved_by_id,
            previous_version_id=entity.previous_version_id,
            change_rationale=entity.change_rationale,
            created_at=entity.created_at,
        )


class StrategicObjectiveModel(Base):
    __tablename__ = "strategic_objectives"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    target_metric: Mapped[str] = mapped_column(String(64), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    current_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> StrategicObjective:
        return StrategicObjective(
            id=self.id,
            company_id=self.company_id,
            title=self.title,
            description=self.description,
            target_metric=self.target_metric,
            target_value=self.target_value,
            current_value=self.current_value,
            priority=self.priority,
            status=self.status,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: StrategicObjective) -> "StrategicObjectiveModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            title=entity.title,
            description=entity.description,
            target_metric=entity.target_metric,
            target_value=entity.target_value,
            current_value=entity.current_value,
            priority=entity.priority,
            status=entity.status,
            created_at=entity.created_at,
        )


class StrategicInitiativeModel(Base):
    __tablename__ = "strategic_initiatives"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    strategic_objective_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lead_department_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    project_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    budget_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=1000000)
    spent_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> StrategicInitiative:
        return StrategicInitiative(
            id=self.id,
            strategic_objective_id=self.strategic_objective_id,
            title=self.title,
            description=self.description,
            lead_department_id=self.lead_department_id,
            project_ids=json.loads(self.project_ids_json) if self.project_ids_json else [],
            status=self.status,
            budget_tokens=self.budget_tokens,
            spent_tokens=self.spent_tokens,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: StrategicInitiative) -> "StrategicInitiativeModel":
        return cls(
            id=entity.id,
            strategic_objective_id=entity.strategic_objective_id,
            title=entity.title,
            description=entity.description,
            lead_department_id=entity.lead_department_id,
            project_ids_json=json.dumps(entity.project_ids),
            status=entity.status,
            budget_tokens=entity.budget_tokens,
            spent_tokens=entity.spent_tokens,
            created_at=entity.created_at,
        )


class CompanyMetricSnapshotModel(Base):
    __tablename__ = "company_metric_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPANY")
    scope_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trend: Mapped[str] = mapped_column(String(32), nullable=False, default="STABLE")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    freshness_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provenance_sources_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> CompanyKPISnapshot:
        return CompanyKPISnapshot(
            id=self.id,
            company_id=self.company_id,
            metric_name=self.metric_name,
            value=self.value,
            target_value=self.target_value,
            scope=self.scope,
            scope_id=self.scope_id,
            trend=MetricTrend(self.trend),
            confidence=self.confidence,
            freshness_seconds=self.freshness_seconds,
            provenance_sources=json.loads(self.provenance_sources_json) if self.provenance_sources_json else [],
            timestamp=self.timestamp,
        )

    @classmethod
    def from_domain(cls, entity: CompanyKPISnapshot) -> "CompanyMetricSnapshotModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            metric_name=entity.metric_name,
            value=entity.value,
            target_value=entity.target_value,
            scope=entity.scope,
            scope_id=entity.scope_id,
            trend=entity.trend.value if isinstance(entity.trend, Enum) else str(entity.trend),
            confidence=entity.confidence,
            freshness_seconds=entity.freshness_seconds,
            provenance_sources_json=json.dumps(entity.provenance_sources),
            timestamp=entity.timestamp,
        )


class CompanyHealthSnapshotModel(Base):
    __tablename__ = "company_health_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operational_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    execution_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    delivery_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    quality_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    workforce_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    reliability_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    resource_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    governance_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    security_health: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    overall_status: Mapped[str] = mapped_column(String(32), nullable=False, default="HEALTHY")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> CompanyHealthSnapshot:
        return CompanyHealthSnapshot(
            id=self.id,
            company_id=self.company_id,
            operational_health=self.operational_health,
            execution_health=self.execution_health,
            delivery_health=self.delivery_health,
            quality_health=self.quality_health,
            workforce_health=self.workforce_health,
            reliability_health=self.reliability_health,
            resource_health=self.resource_health,
            governance_health=self.governance_health,
            security_health=self.security_health,
            overall_status=CompanyHealthStatus(self.overall_status),
            explanation=self.explanation,
            evaluated_at=self.evaluated_at,
        )

    @classmethod
    def from_domain(cls, entity: CompanyHealthSnapshot) -> "CompanyHealthSnapshotModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            operational_health=entity.operational_health,
            execution_health=entity.execution_health,
            delivery_health=entity.delivery_health,
            quality_health=entity.quality_health,
            workforce_health=entity.workforce_health,
            reliability_health=entity.reliability_health,
            resource_health=entity.resource_health,
            governance_health=entity.governance_health,
            security_health=entity.security_health,
            overall_status=entity.overall_status.value if isinstance(entity.overall_status, Enum) else str(entity.overall_status),
            explanation=entity.explanation,
            evaluated_at=entity.evaluated_at,
        )


class CompanyRiskModel(Base):
    __tablename__ = "company_risks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="OPERATIONAL")
    probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    impact: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="LOW")
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    affected_entity_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    mitigation_plan: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> CompanyRisk:
        return CompanyRisk(
            id=self.id,
            company_id=self.company_id,
            title=self.title,
            category=self.category,
            probability=self.probability,
            impact=self.impact,
            severity=RiskSeverity(self.severity),
            evidence_ids=json.loads(self.evidence_ids_json) if self.evidence_ids_json else [],
            affected_entity_ids=json.loads(self.affected_entity_ids_json) if self.affected_entity_ids_json else [],
            mitigation_plan=self.mitigation_plan,
            status=self.status,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: CompanyRisk) -> "CompanyRiskModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            title=entity.title,
            category=entity.category,
            probability=entity.probability,
            impact=entity.impact,
            severity=entity.severity.value if isinstance(entity.severity, Enum) else str(entity.severity),
            evidence_ids_json=json.dumps(entity.evidence_ids),
            affected_entity_ids_json=json.dumps(entity.affected_entity_ids),
            mitigation_plan=entity.mitigation_plan,
            status=entity.status,
            created_at=entity.created_at,
        )


class CompanyOpportunityModel(Base):
    __tablename__ = "company_opportunities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="EFFICIENCY")
    expected_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    required_resources: Mapped[str] = mapped_column(Text, nullable=False, default="")
    affected_objective_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> CompanyOpportunity:
        return CompanyOpportunity(
            id=self.id,
            company_id=self.company_id,
            title=self.title,
            category=self.category,
            expected_value=self.expected_value,
            required_resources=self.required_resources,
            affected_objective_ids=json.loads(self.affected_objective_ids_json) if self.affected_objective_ids_json else [],
            evidence_ids=json.loads(self.evidence_ids_json) if self.evidence_ids_json else [],
            confidence=self.confidence,
            status=self.status,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: CompanyOpportunity) -> "CompanyOpportunityModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            title=entity.title,
            category=entity.category,
            expected_value=entity.expected_value,
            required_resources=entity.required_resources,
            affected_objective_ids_json=json.dumps(entity.affected_objective_ids),
            evidence_ids_json=json.dumps(entity.evidence_ids),
            confidence=entity.confidence,
            status=entity.status,
            created_at=entity.created_at,
        )


class StrategicAnalysisModel(Base):
    __tablename__ = "strategic_analyses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cycle_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    current_situation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    observed_facts_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    trends_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    risks_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    opportunities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    constraints_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    potential_causes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    alternatives_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    required_resources: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    model_used: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> StrategicAnalysis:
        return StrategicAnalysis(
            id=self.id,
            company_id=self.company_id,
            cycle_id=self.cycle_id,
            current_situation=self.current_situation,
            observed_facts=json.loads(self.observed_facts_json) if self.observed_facts_json else [],
            trends=json.loads(self.trends_json) if self.trends_json else [],
            risks=json.loads(self.risks_json) if self.risks_json else [],
            opportunities=json.loads(self.opportunities_json) if self.opportunities_json else [],
            constraints=json.loads(self.constraints_json) if self.constraints_json else [],
            potential_causes=json.loads(self.potential_causes_json) if self.potential_causes_json else [],
            alternatives=json.loads(self.alternatives_json) if self.alternatives_json else [],
            required_resources=self.required_resources,
            confidence=self.confidence,
            evidence_ids=json.loads(self.evidence_ids_json) if self.evidence_ids_json else [],
            model_used=self.model_used,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: StrategicAnalysis) -> "StrategicAnalysisModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            cycle_id=entity.cycle_id,
            current_situation=entity.current_situation,
            observed_facts_json=json.dumps(entity.observed_facts),
            trends_json=json.dumps(entity.trends),
            risks_json=json.dumps(entity.risks),
            opportunities_json=json.dumps(entity.opportunities),
            constraints_json=json.dumps(entity.constraints),
            potential_causes_json=json.dumps(entity.potential_causes),
            alternatives_json=json.dumps(entity.alternatives),
            required_resources=entity.required_resources,
            confidence=entity.confidence,
            evidence_ids_json=json.dumps(entity.evidence_ids),
            model_used=entity.model_used,
            created_at=entity.created_at,
        )


class StrategyProposalModel(Base):
    __tablename__ = "strategy_proposals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    proposal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    proposal: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    benefits: Mapped[str] = mapped_column(Text, nullable=False, default="")
    resource_impact: Mapped[str] = mapped_column(Text, nullable=False, default="")
    risks_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    dependencies_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    affected_departments_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    reversibility: Mapped[str] = mapped_column(String(32), nullable=False, default="HIGH")
    governance_level: Mapped[str] = mapped_column(String(64), nullable=False, default="MANAGER_APPROVAL")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    proposed_by_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    governance_approval_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> StrategyProposal:
        return StrategyProposal(
            id=self.id,
            company_id=self.company_id,
            proposal_type=StrategyProposalType(self.proposal_type),
            title=self.title,
            proposal=self.proposal,
            reason=self.reason,
            evidence_ids=json.loads(self.evidence_ids_json) if self.evidence_ids_json else [],
            benefits=self.benefits,
            resource_impact=self.resource_impact,
            risks=json.loads(self.risks_json) if self.risks_json else [],
            dependencies=json.loads(self.dependencies_json) if self.dependencies_json else [],
            affected_departments=json.loads(self.affected_departments_json) if self.affected_departments_json else [],
            reversibility=self.reversibility,
            governance_level=self.governance_level,
            confidence=self.confidence,
            status=StrategyProposalStatus(self.status),
            proposed_by_id=self.proposed_by_id,
            governance_approval_id=self.governance_approval_id,
            created_at=self.created_at,
            processed_at=self.processed_at,
        )

    @classmethod
    def from_domain(cls, entity: StrategyProposal) -> "StrategyProposalModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            proposal_type=entity.proposal_type.value if isinstance(entity.proposal_type, Enum) else str(entity.proposal_type),
            title=entity.title,
            proposal=entity.proposal,
            reason=entity.reason,
            evidence_ids_json=json.dumps(entity.evidence_ids),
            benefits=entity.benefits,
            resource_impact=entity.resource_impact,
            risks_json=json.dumps(entity.risks),
            dependencies_json=json.dumps(entity.dependencies),
            affected_departments_json=json.dumps(entity.affected_departments),
            reversibility=entity.reversibility,
            governance_level=entity.governance_level,
            confidence=entity.confidence,
            status=entity.status.value if isinstance(entity.status, Enum) else str(entity.status),
            proposed_by_id=entity.proposed_by_id,
            governance_approval_id=entity.governance_approval_id,
            created_at=entity.created_at,
            processed_at=entity.processed_at,
        )


class PortfolioItemModel(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False, default="PROJECT")
    reference_id: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    progress_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    resource_utilization_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    has_bottleneck: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bottleneck_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> PortfolioItem:
        return PortfolioItem(
            id=self.id,
            company_id=self.company_id,
            title=self.title,
            item_type=self.item_type,
            reference_id=self.reference_id,
            priority=self.priority,
            progress_pct=self.progress_pct,
            resource_utilization_pct=self.resource_utilization_pct,
            status=self.status,
            has_bottleneck=self.has_bottleneck,
            bottleneck_description=self.bottleneck_description,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: PortfolioItem) -> "PortfolioItemModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            title=entity.title,
            item_type=entity.item_type,
            reference_id=entity.reference_id,
            priority=entity.priority,
            progress_pct=entity.progress_pct,
            resource_utilization_pct=entity.resource_utilization_pct,
            status=entity.status,
            has_bottleneck=entity.has_bottleneck,
            bottleneck_description=entity.bottleneck_description,
            created_at=entity.created_at,
        )


class ResourceAllocationPlanModel(Base):
    __tablename__ = "resource_allocation_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    cycle_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    demand_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    allocations_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    constraints_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    tradeoffs_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> ResourceAllocationPlan:
        return ResourceAllocationPlan(
            id=self.id,
            company_id=self.company_id,
            cycle_id=self.cycle_id,
            demand_summary=self.demand_summary,
            allocations_json=json.loads(self.allocations_json) if self.allocations_json else {},
            constraints_json=json.loads(self.constraints_json) if self.constraints_json else {},
            tradeoffs_summary=self.tradeoffs_summary,
            is_approved=self.is_approved,
            approved_by_id=self.approved_by_id,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: ResourceAllocationPlan) -> "ResourceAllocationPlanModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            cycle_id=entity.cycle_id,
            demand_summary=entity.demand_summary,
            allocations_json=json.dumps(entity.allocations_json),
            constraints_json=json.dumps(entity.constraints_json),
            tradeoffs_summary=entity.tradeoffs_summary,
            is_approved=entity.is_approved,
            approved_by_id=entity.approved_by_id,
            created_at=entity.created_at,
        )


class ContinuousImprovementProposalModel(Base):
    __tablename__ = "continuous_improvement_proposals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="PROCESS")
    source_event_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    proposed_change: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, nullable=False, default="")
    governance_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> ContinuousImprovementProposal:
        return ContinuousImprovementProposal(
            id=self.id,
            company_id=self.company_id,
            title=self.title,
            category=self.category,
            source_event_ids=json.loads(self.source_event_ids_json) if self.source_event_ids_json else [],
            proposed_change=self.proposed_change,
            expected_impact=self.expected_impact,
            governance_required=self.governance_required,
            status=self.status,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: ContinuousImprovementProposal) -> "ContinuousImprovementProposalModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            title=entity.title,
            category=entity.category,
            source_event_ids_json=json.dumps(entity.source_event_ids),
            proposed_change=entity.proposed_change,
            expected_impact=entity.expected_impact,
            governance_required=entity.governance_required,
            status=entity.status,
            created_at=entity.created_at,
        )


class StrategySimulationModel(Base):
    __tablename__ = "strategy_simulations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    assumptions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    input_parameters_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    projected_outcomes_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    resource_effects_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    projected_risks_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_authoritative: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> StrategySimulation:
        return StrategySimulation(
            id=self.id,
            company_id=self.company_id,
            title=self.title,
            assumptions=json.loads(self.assumptions_json) if self.assumptions_json else [],
            input_parameters=json.loads(self.input_parameters_json) if self.input_parameters_json else {},
            projected_outcomes=json.loads(self.projected_outcomes_json) if self.projected_outcomes_json else {},
            resource_effects=json.loads(self.resource_effects_json) if self.resource_effects_json else {},
            projected_risks=json.loads(self.projected_risks_json) if self.projected_risks_json else [],
            confidence=self.confidence,
            is_authoritative=False,  # Enforce false invariant
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: StrategySimulation) -> "StrategySimulationModel":
        return cls(
            id=entity.id,
            company_id=entity.company_id,
            title=entity.title,
            assumptions_json=json.dumps(entity.assumptions),
            input_parameters_json=json.dumps(entity.input_parameters),
            projected_outcomes_json=json.dumps(entity.projected_outcomes),
            resource_effects_json=json.dumps(entity.resource_effects),
            projected_risks_json=json.dumps(entity.projected_risks),
            confidence=entity.confidence,
            is_authoritative=False,
            created_at=entity.created_at,
        )


# --- Phase 25 Multi-Company & Simulation ORM Models ---

class CompanyModel(Base):
    __tablename__ = "company_tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    company_type: Mapped[str] = mapped_column(String(32), nullable=False, default="AUTONOMOUS")
    industry: Mapped[str] = mapped_column(String(64), nullable=False, default="TECHNOLOGY")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(32), nullable=False, default="en_US")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    lifecycle: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, default="SYSTEM")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class CompanyProfileModel(Base):
    __tablename__ = "company_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operating_hours: Mapped[str] = mapped_column(String(64), nullable=False, default="24/7")
    model_routing_policy_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    tool_policy_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    governance_defaults_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    workforce_config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class CompanyMembershipModel(Base):
    __tablename__ = "company_memberships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="VIEWER")
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class CompanyTemplateModel(Base):
    __tablename__ = "company_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    industry: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    structure_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    default_departments_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    default_roles_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class CompanyRelationshipModel(Base):
    __tablename__ = "company_relationships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_a_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    company_b_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False, default="PARTNER")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class CompanyDataShareRequestModel(Base):
    __tablename__ = "company_data_share_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    data_scope: Mapped[str] = mapped_column(String(32), nullable=False, default="READ_ONLY")
    purpose: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="REQUESTED")
    governance_approval_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CompanyResourceQuotaModel(Base):
    __tablename__ = "company_resource_quotas"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    max_concurrent_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_concurrent_agents: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    max_monthly_model_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=100000)
    max_storage_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=50000)
    max_simulations: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class CompanyResourceUsageModel(Base):
    __tablename__ = "company_resource_usages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    active_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_agents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_model_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_simulations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class CompanySimulationModel(Base):
    __tablename__ = "company_simulations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="SIMULATION")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, default="SYSTEM")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class SimulationSnapshotModel(Base):
    __tablename__ = "simulation_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    snapshot_name: Mapped[str] = mapped_column(String(128), nullable=False)
    snapshot_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class SimulationScenarioModel(Base):
    __tablename__ = "simulation_scenarios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    variables_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class SimulationResultModel(Base):
    __tablename__ = "simulation_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scenario_name: Mapped[str] = mapped_column(String(128), nullable=False)
    baseline_metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    simulated_metrics_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    variance_analysis_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.90)
    produced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class SimulationFinancialRecordModel(Base):
    __tablename__ = "simulation_financial_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(64), nullable=False, default="SIMULATED_REVENUE")
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

