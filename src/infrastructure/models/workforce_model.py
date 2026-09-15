"""SQLAlchemy ORM Models for Workforce Demands, Capacity, Gaps, Recommendations, and Plans."""

import json
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.workforce import (
    CapabilityGap,
    CapacitySnapshot,
    EmployeeTemplate,
    GapSeverity,
    StaffingPlanStatus,
    StaffingRecommendation,
    WorkforceAllocation,
    WorkforceChangeRequest,
    WorkforceChangeRequestStatus,
    WorkforceChangeRequestType,
    WorkforceDecision,
    WorkforceDemand,
    WorkforcePlan,
)
from src.infrastructure.database import Base


class WorkforceDemandModel(Base):
    __tablename__ = "workforce_demands"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    department_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False, default="LOW")
    governance_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> WorkforceDemand:
        return WorkforceDemand(
            id=self.id,
            source_type=self.source_type,
            source_id=self.source_id,
            department_id=self.department_id,
            capability=self.capability,
            required_count=self.required_count,
            priority=self.priority,
            duration_days=self.duration_days,
            deadline=self.deadline,
            risk_level=self.risk_level,
            governance_required=self.governance_required,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: WorkforceDemand) -> "WorkforceDemandModel":
        return cls(
            id=entity.id,
            source_type=entity.source_type,
            source_id=entity.source_id,
            department_id=entity.department_id,
            capability=entity.capability,
            required_count=entity.required_count,
            priority=entity.priority,
            duration_days=entity.duration_days,
            deadline=entity.deadline,
            risk_level=entity.risk_level,
            governance_required=entity.governance_required,
            created_at=entity.created_at,
        )


class CapacitySnapshotModel(Base):
    __tablename__ = "capacity_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    max_capacity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    allocated_capacity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    available_capacity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    active_assignments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> CapacitySnapshot:
        return CapacitySnapshot(
            id=self.id,
            employee_id=self.employee_id,
            capability=self.capability,
            max_capacity=self.max_capacity,
            allocated_capacity=self.allocated_capacity,
            available_capacity=self.available_capacity,
            active_assignments_count=self.active_assignments_count,
            snapshot_time=self.snapshot_time,
        )

    @classmethod
    def from_domain(cls, entity: CapacitySnapshot) -> "CapacitySnapshotModel":
        return cls(
            id=entity.id,
            employee_id=entity.employee_id,
            capability=entity.capability,
            max_capacity=entity.max_capacity,
            allocated_capacity=entity.allocated_capacity,
            available_capacity=entity.available_capacity,
            active_assignments_count=entity.active_assignments_count,
            snapshot_time=entity.snapshot_time,
        )


class CapabilityGapModel(Base):
    __tablename__ = "capability_gaps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    capability: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    required_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="LOW")
    affected_project_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> CapabilityGap:
        projects = json.loads(self.affected_project_ids_json) if self.affected_project_ids_json else []
        return CapabilityGap(
            id=self.id,
            capability=self.capability,
            required_count=self.required_count,
            available_count=self.available_count,
            gap_count=self.gap_count,
            severity=GapSeverity(self.severity),
            affected_project_ids=projects,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: CapabilityGap) -> "CapabilityGapModel":
        return cls(
            id=entity.id,
            capability=entity.capability,
            required_count=entity.required_count,
            available_count=entity.available_count,
            gap_count=entity.gap_count,
            severity=entity.severity.value if isinstance(entity.severity, Enum) else str(entity.severity),
            affected_project_ids_json=json.dumps(entity.affected_project_ids),
            created_at=entity.created_at,
        )


class StaffingRecommendationModel(Base):
    __tablename__ = "staffing_recommendations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    demand_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    candidate_employee_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    capability_fit_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    availability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    workload_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    context_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    penalty_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> StaffingRecommendation:
        cands = json.loads(self.candidate_employee_ids_json) if self.candidate_employee_ids_json else []
        return StaffingRecommendation(
            id=self.id,
            demand_id=self.demand_id,
            candidate_employee_ids=cands,
            capability_fit_score=self.capability_fit_score,
            availability_score=self.availability_score,
            workload_score=self.workload_score,
            reliability_score=self.reliability_score,
            context_score=self.context_score,
            penalty_score=self.penalty_score,
            final_score=self.final_score,
            reasoning=self.reasoning,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: StaffingRecommendation) -> "StaffingRecommendationModel":
        return cls(
            id=entity.id,
            demand_id=entity.demand_id,
            candidate_employee_ids_json=json.dumps(entity.candidate_employee_ids),
            capability_fit_score=entity.capability_fit_score,
            availability_score=entity.availability_score,
            workload_score=entity.workload_score,
            reliability_score=entity.reliability_score,
            context_score=entity.context_score,
            penalty_score=entity.penalty_score,
            final_score=entity.final_score,
            reasoning=entity.reasoning,
            created_at=entity.created_at,
        )


class WorkforceAllocationModel(Base):
    __tablename__ = "workforce_allocations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    team_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    department_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    allocation_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    is_temporary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    def to_domain(self) -> WorkforceAllocation:
        return WorkforceAllocation(
            id=self.id,
            employee_id=self.employee_id,
            team_id=self.team_id,
            project_id=self.project_id,
            department_id=self.department_id,
            allocation_percentage=self.allocation_percentage,
            is_temporary=self.is_temporary,
            start_time=self.start_time,
            end_time=self.end_time,
            status=self.status,
        )

    @classmethod
    def from_domain(cls, entity: WorkforceAllocation) -> "WorkforceAllocationModel":
        return cls(
            id=entity.id,
            employee_id=entity.employee_id,
            team_id=entity.team_id,
            project_id=entity.project_id,
            department_id=entity.department_id,
            allocation_percentage=entity.allocation_percentage,
            is_temporary=entity.is_temporary,
            start_time=entity.start_time,
            end_time=entity.end_time,
            status=entity.status,
        )


class WorkforceChangeRequestModel(Base):
    __tablename__ = "workforce_change_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_by_id: Mapped[str] = mapped_column(String(64), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    governance_approval_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> WorkforceChangeRequest:
        return WorkforceChangeRequest(
            id=self.id,
            request_type=WorkforceChangeRequestType(self.request_type),
            target_id=self.target_id,
            requested_by_id=self.requested_by_id,
            justification=self.justification,
            governance_approval_id=self.governance_approval_id,
            status=WorkforceChangeRequestStatus(self.status),
            created_at=self.created_at,
            processed_at=self.processed_at,
        )

    @classmethod
    def from_domain(cls, entity: WorkforceChangeRequest) -> "WorkforceChangeRequestModel":
        return cls(
            id=entity.id,
            request_type=entity.request_type.value if hasattr(entity.request_type, "value") else str(entity.request_type),
            target_id=entity.target_id,
            requested_by_id=entity.requested_by_id,
            justification=entity.justification,
            governance_approval_id=entity.governance_approval_id,
            status=entity.status.value if hasattr(entity.status, "value") else str(entity.status),
            created_at=entity.created_at,
            processed_at=entity.processed_at,
        )


class WorkforceDecisionModel(Base):
    __tablename__ = "workforce_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    change_request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    recommendation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    manager_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    human_approver_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_type: Mapped[str] = mapped_column(String(32), nullable=False, default="APPROVED")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    policy_applied: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    def to_domain(self) -> WorkforceDecision:
        return WorkforceDecision(
            id=self.id,
            change_request_id=self.change_request_id,
            recommendation_id=self.recommendation_id,
            actor_id=self.actor_id,
            manager_id=self.manager_id,
            human_approver_id=self.human_approver_id,
            decision_type=self.decision_type,
            reason=self.reason,
            policy_applied=self.policy_applied,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: WorkforceDecision) -> "WorkforceDecisionModel":
        return cls(
            id=entity.id,
            change_request_id=entity.change_request_id,
            recommendation_id=entity.recommendation_id,
            actor_id=entity.actor_id,
            manager_id=entity.manager_id,
            human_approver_id=entity.human_approver_id,
            decision_type=entity.decision_type,
            reason=entity.reason,
            policy_applied=entity.policy_applied,
            created_at=entity.created_at,
        )


class EmployeeTemplateModel(Base):
    __tablename__ = "employee_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    capabilities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    skills_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    responsibilities_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    default_permissions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    department_compatibility_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    governance_requirements_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    default_agent_config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    def to_domain(self) -> EmployeeTemplate:
        return EmployeeTemplate(
            id=self.id,
            title=self.title,
            role=self.role,
            capabilities=json.loads(self.capabilities_json) if self.capabilities_json else [],
            skills=json.loads(self.skills_json) if self.skills_json else [],
            responsibilities=json.loads(self.responsibilities_json) if self.responsibilities_json else [],
            default_permissions=json.loads(self.default_permissions_json) if self.default_permissions_json else [],
            department_compatibility=json.loads(self.department_compatibility_json) if self.department_compatibility_json else [],
            governance_requirements=json.loads(self.governance_requirements_json) if self.governance_requirements_json else [],
            default_agent_config=json.loads(self.default_agent_config_json) if self.default_agent_config_json else {},
        )

    @classmethod
    def from_domain(cls, entity: EmployeeTemplate) -> "EmployeeTemplateModel":
        return cls(
            id=entity.id,
            title=entity.title,
            role=entity.role,
            capabilities_json=json.dumps(entity.capabilities),
            skills_json=json.dumps(entity.skills),
            responsibilities_json=json.dumps(entity.responsibilities),
            default_permissions_json=json.dumps(entity.default_permissions),
            department_compatibility_json=json.dumps(entity.department_compatibility),
            governance_requirements_json=json.dumps(entity.governance_requirements),
            default_agent_config_json=json.dumps(entity.default_agent_config),
        )


class WorkforcePlanModel(Base):
    __tablename__ = "workforce_plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    planning_horizon: Mapped[str] = mapped_column(String(32), nullable=False, default="Q1")
    objectives_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    demand_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    capacity_snapshot_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    gap_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    recommendation_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_domain(self) -> WorkforcePlan:
        return WorkforcePlan(
            id=self.id,
            planning_horizon=self.planning_horizon,
            objectives=json.loads(self.objectives_json) if self.objectives_json else [],
            demand_ids=json.loads(self.demand_ids_json) if self.demand_ids_json else [],
            capacity_snapshot_ids=json.loads(self.capacity_snapshot_ids_json) if self.capacity_snapshot_ids_json else [],
            gap_ids=json.loads(self.gap_ids_json) if self.gap_ids_json else [],
            recommendation_ids=json.loads(self.recommendation_ids_json) if self.recommendation_ids_json else [],
            status=StaffingPlanStatus(self.status),
            created_at=self.created_at,
            approved_at=self.approved_at,
        )

    @classmethod
    def from_domain(cls, entity: WorkforcePlan) -> "WorkforcePlanModel":
        return cls(
            id=entity.id,
            planning_horizon=entity.planning_horizon,
            objectives_json=json.dumps(entity.objectives),
            demand_ids_json=json.dumps(entity.demand_ids),
            capacity_snapshot_ids_json=json.dumps(entity.capacity_snapshot_ids),
            gap_ids_json=json.dumps(entity.gap_ids),
            recommendation_ids_json=json.dumps(entity.recommendation_ids),
            status=entity.status.value if hasattr(entity.status, "value") else str(entity.status),
            created_at=entity.created_at,
            approved_at=entity.approved_at,
        )
