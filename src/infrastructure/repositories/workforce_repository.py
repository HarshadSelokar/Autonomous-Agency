"""SQLAlchemy Repository for Workforce entities."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.workforce import (
    CapabilityGap,
    CapacitySnapshot,
    EmployeeTemplate,
    StaffingRecommendation,
    WorkforceAllocation,
    WorkforceChangeRequest,
    WorkforceDecision,
    WorkforceDemand,
    WorkforcePlan,
)
from src.infrastructure.models.workforce_model import (
    CapabilityGapModel,
    CapacitySnapshotModel,
    EmployeeTemplateModel,
    StaffingRecommendationModel,
    WorkforceAllocationModel,
    WorkforceChangeRequestModel,
    WorkforceDecisionModel,
    WorkforceDemandModel,
    WorkforcePlanModel,
)


class SQLAlchemyWorkforceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Workforce Demand ---
    async def save_demand(self, demand: WorkforceDemand) -> WorkforceDemand:
        model = await self.session.get(WorkforceDemandModel, demand.id)
        if model is None:
            model = WorkforceDemandModel.from_domain(demand)
            self.session.add(model)
        else:
            updated = WorkforceDemandModel.from_domain(demand)
            model.source_type = updated.source_type
            model.source_id = updated.source_id
            model.department_id = updated.department_id
            model.capability = updated.capability
            model.required_count = updated.required_count
            model.priority = updated.priority
            model.duration_days = updated.duration_days
            model.deadline = updated.deadline
            model.risk_level = updated.risk_level
            model.governance_required = updated.governance_required
        await self.session.commit()
        return model.to_domain()

    async def get_demand(self, demand_id: str) -> WorkforceDemand | None:
        model = await self.session.get(WorkforceDemandModel, demand_id)
        return model.to_domain() if model else None

    async def list_demands(self) -> list[WorkforceDemand]:
        stmt = select(WorkforceDemandModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    # --- Capacity Snapshot ---
    async def save_capacity_snapshot(self, snapshot: CapacitySnapshot) -> CapacitySnapshot:
        model = await self.session.get(CapacitySnapshotModel, snapshot.id)
        if model is None:
            model = CapacitySnapshotModel.from_domain(snapshot)
            self.session.add(model)
        else:
            updated = CapacitySnapshotModel.from_domain(snapshot)
            model.allocated_capacity = updated.allocated_capacity
            model.available_capacity = updated.available_capacity
            model.active_assignments_count = updated.active_assignments_count
            model.snapshot_time = updated.snapshot_time
        await self.session.commit()
        return model.to_domain()

    async def list_capacity_snapshots(self) -> list[CapacitySnapshot]:
        stmt = select(CapacitySnapshotModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    async def get_capacity_by_employee(self, employee_id: str) -> list[CapacitySnapshot]:
        stmt = select(CapacitySnapshotModel).where(CapacitySnapshotModel.employee_id == employee_id)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    # --- Capability Gap ---
    async def save_capability_gap(self, gap: CapabilityGap) -> CapabilityGap:
        model = await self.session.get(CapabilityGapModel, gap.id)
        if model is None:
            model = CapabilityGapModel.from_domain(gap)
            self.session.add(model)
        else:
            updated = CapabilityGapModel.from_domain(gap)
            model.required_count = updated.required_count
            model.available_count = updated.available_count
            model.gap_count = updated.gap_count
            model.severity = updated.severity
            model.affected_project_ids_json = updated.affected_project_ids_json
        await self.session.commit()
        return model.to_domain()

    async def list_capability_gaps(self) -> list[CapabilityGap]:
        stmt = select(CapabilityGapModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    # --- Staffing Recommendation ---
    async def save_recommendation(self, rec: StaffingRecommendation) -> StaffingRecommendation:
        model = await self.session.get(StaffingRecommendationModel, rec.id)
        if model is None:
            model = StaffingRecommendationModel.from_domain(rec)
            self.session.add(model)
        else:
            updated = StaffingRecommendationModel.from_domain(rec)
            model.candidate_employee_ids_json = updated.candidate_employee_ids_json
            model.final_score = updated.final_score
            model.reasoning = updated.reasoning
        await self.session.commit()
        return model.to_domain()

    async def get_recommendation(self, rec_id: str) -> StaffingRecommendation | None:
        model = await self.session.get(StaffingRecommendationModel, rec_id)
        return model.to_domain() if model else None

    async def list_recommendations(self) -> list[StaffingRecommendation]:
        stmt = select(StaffingRecommendationModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    # --- Workforce Allocation ---
    async def save_allocation(self, alloc: WorkforceAllocation) -> WorkforceAllocation:
        model = await self.session.get(WorkforceAllocationModel, alloc.id)
        if model is None:
            model = WorkforceAllocationModel.from_domain(alloc)
            self.session.add(model)
        else:
            updated = WorkforceAllocationModel.from_domain(alloc)
            model.team_id = updated.team_id
            model.project_id = updated.project_id
            model.allocation_percentage = updated.allocation_percentage
            model.status = updated.status
            model.end_time = updated.end_time
        await self.session.commit()
        return model.to_domain()

    async def list_allocations(self) -> list[WorkforceAllocation]:
        stmt = select(WorkforceAllocationModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    async def list_allocations_by_employee(self, employee_id: str) -> list[WorkforceAllocation]:
        stmt = select(WorkforceAllocationModel).where(WorkforceAllocationModel.employee_id == employee_id)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    # --- Workforce Change Request ---
    async def save_change_request(self, req: WorkforceChangeRequest) -> WorkforceChangeRequest:
        model = await self.session.get(WorkforceChangeRequestModel, req.id)
        if model is None:
            model = WorkforceChangeRequestModel.from_domain(req)
            self.session.add(model)
        else:
            updated = WorkforceChangeRequestModel.from_domain(req)
            model.status = updated.status
            model.governance_approval_id = updated.governance_approval_id
            model.processed_at = updated.processed_at
        await self.session.commit()
        return model.to_domain()

    async def get_change_request(self, req_id: str) -> WorkforceChangeRequest | None:
        model = await self.session.get(WorkforceChangeRequestModel, req_id)
        return model.to_domain() if model else None

    async def list_change_requests(self) -> list[WorkforceChangeRequest]:
        stmt = select(WorkforceChangeRequestModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    # --- Workforce Decision ---
    async def save_decision(self, dec: WorkforceDecision) -> WorkforceDecision:
        model = await self.session.get(WorkforceDecisionModel, dec.id)
        if model is None:
            model = WorkforceDecisionModel.from_domain(dec)
            self.session.add(model)
        else:
            updated = WorkforceDecisionModel.from_domain(dec)
            model.decision_type = updated.decision_type
            model.reason = updated.reason
        await self.session.commit()
        return model.to_domain()

    async def list_decisions(self) -> list[WorkforceDecision]:
        stmt = select(WorkforceDecisionModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    # --- Employee Template ---
    async def save_employee_template(self, tpl: EmployeeTemplate) -> EmployeeTemplate:
        model = await self.session.get(EmployeeTemplateModel, tpl.id)
        if model is None:
            model = EmployeeTemplateModel.from_domain(tpl)
            self.session.add(model)
        else:
            updated = EmployeeTemplateModel.from_domain(tpl)
            model.title = updated.title
            model.capabilities_json = updated.capabilities_json
            model.skills_json = updated.skills_json
        await self.session.commit()
        return model.to_domain()

    async def list_employee_templates(self) -> list[EmployeeTemplate]:
        stmt = select(EmployeeTemplateModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]

    # --- Workforce Plan ---
    async def save_plan(self, plan: WorkforcePlan) -> WorkforcePlan:
        model = await self.session.get(WorkforcePlanModel, plan.id)
        if model is None:
            model = WorkforcePlanModel.from_domain(plan)
            self.session.add(model)
        else:
            updated = WorkforcePlanModel.from_domain(plan)
            model.status = updated.status
            model.approved_at = updated.approved_at
        await self.session.commit()
        return model.to_domain()

    async def get_plan(self, plan_id: str) -> WorkforcePlan | None:
        model = await self.session.get(WorkforcePlanModel, plan_id)
        return model.to_domain() if model else None

    async def list_plans(self) -> list[WorkforcePlan]:
        stmt = select(WorkforcePlanModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]
