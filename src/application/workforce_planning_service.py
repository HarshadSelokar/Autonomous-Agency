"""
Workforce Planning Service.

Handles demand analysis, employee capacity snapshots, capability gap detection,
staffing recommendation generation with explainable scoring, and workforce planning.
"""

import logging
from datetime import datetime

from src.application.employee_selector import EmployeeSelector
from src.domain.employee import Employee
from src.domain.events import (
    CapabilityGapDetectedEvent,
    StaffingPlanCreatedEvent,
    StaffingRecommendationCreatedEvent,
    WorkforceDemandCreatedEvent,
)
from src.domain.workforce import (
    CapabilityGap,
    CapacitySnapshot,
    GapSeverity,
    StaffingPlanStatus,
    StaffingRecommendation,
    WorkforceDemand,
    WorkforcePlan,
)
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository
from src.infrastructure.repositories.workforce_repository import SQLAlchemyWorkforceRepository

logger = logging.getLogger(__name__)


class WorkforcePlanningService:
    def __init__(
        self,
        workforce_repo: SQLAlchemyWorkforceRepository,
        outbox_repo: SQLAlchemyOutboxRepository | None = None,
        employee_selector: EmployeeSelector | None = None,
    ) -> None:
        self.workforce_repo = workforce_repo
        self.outbox_repo = outbox_repo
        self.employee_selector = employee_selector or EmployeeSelector()

    async def create_workforce_demand(
        self,
        source_type: str,
        source_id: str,
        capability: str,
        required_count: int = 1,
        priority: int = 1,
        department_id: str | None = None,
        duration_days: int = 30,
        deadline: datetime | None = None,
        risk_level: str = "LOW",
        governance_required: bool = False,
    ) -> WorkforceDemand:
        demand = WorkforceDemand(
            source_type=source_type,
            source_id=source_id,
            department_id=department_id,
            capability=capability,
            required_count=required_count,
            priority=priority,
            duration_days=duration_days,
            deadline=deadline,
            risk_level=risk_level,
            governance_required=governance_required,
        )
        saved = await self.workforce_repo.save_demand(demand)

        if self.outbox_repo:
            evt = WorkforceDemandCreatedEvent(
                demand_id=saved.id,
                source_type=saved.source_type,
                source_id=saved.source_id,
                capability=saved.capability,
                required_count=saved.required_count,
            )
            await self.outbox_repo.save_event(evt)

        return saved

    async def calculate_capacity_snapshots(
        self,
        employees: list[Employee],
        active_allocations_by_emp: dict[str, float] | None = None,
        active_assignments_count_by_emp: dict[str, int] | None = None,
    ) -> list[CapacitySnapshot]:
        """
        Creates deterministic capacity snapshots for each active employee based on
        their capabilities, existing workload allocations, and active tasks.
        """
        alloc_map = active_allocations_by_emp or {}
        task_map = active_assignments_count_by_emp or {}
        snapshots: list[CapacitySnapshot] = []

        for emp in employees:
            if not emp.is_executable():
                continue

            allocated = alloc_map.get(emp.id, 0.0)
            active_tasks = task_map.get(emp.id, 0)
            available = max(0.0, 1.0 - (allocated / 100.0 if allocated > 1.0 else allocated))

            emp_caps = [c.name if hasattr(c, "name") else str(c) for c in emp.capabilities]
            for cap in emp_caps:
                snap = CapacitySnapshot(
                    employee_id=emp.id,
                    capability=cap,
                    max_capacity=1.0,
                    allocated_capacity=1.0 - available,
                    available_capacity=available,
                    active_assignments_count=active_tasks,
                )
                saved = await self.workforce_repo.save_capacity_snapshot(snap)
                snapshots.append(saved)

        return snapshots

    async def detect_capability_gaps(
        self,
        demands: list[WorkforceDemand] | None = None,
        snapshots: list[CapacitySnapshot] | None = None,
    ) -> list[CapabilityGap]:
        """
        Calculates: Demand - Available Capacity = Capability Gap.
        Determines severity based on gap size and highest demand priority.
        """
        if demands is None:
            demands = await self.workforce_repo.list_demands()
        if snapshots is None:
            snapshots = await self.workforce_repo.list_capacity_snapshots()

        # Aggregate demand by capability
        req_by_cap: dict[str, int] = {}
        affected_projects_by_cap: dict[str, set[str]] = {}
        max_priority_by_cap: dict[str, int] = {}

        for d in demands:
            cap = d.capability
            req_by_cap[cap] = req_by_cap.get(cap, 0) + d.required_count
            if d.source_id:
                affected_projects_by_cap.setdefault(cap, set()).add(d.source_id)
            max_priority_by_cap[cap] = max(max_priority_by_cap.get(cap, 1), d.priority)

        # Aggregate available count by capability (where available_capacity >= 0.2)
        avail_by_cap: dict[str, float] = {}
        for s in snapshots:
            if s.available_capacity >= 0.2:
                avail_by_cap[s.capability] = avail_by_cap.get(s.capability, 0.0) + s.available_capacity

        gaps: list[CapabilityGap] = []
        for cap, req_count in req_by_cap.items():
            avail_units = int(avail_by_cap.get(cap, 0.0))
            gap_count = max(0, req_count - avail_units)

            if gap_count > 0:
                prio = max_priority_by_cap.get(cap, 1)
                if prio >= 5 or gap_count >= 4:
                    severity = GapSeverity.CRITICAL
                elif prio >= 4 or gap_count >= 2:
                    severity = GapSeverity.HIGH
                elif prio >= 3:
                    severity = GapSeverity.MEDIUM
                else:
                    severity = GapSeverity.LOW

                gap = CapabilityGap(
                    capability=cap,
                    required_count=req_count,
                    available_count=avail_units,
                    gap_count=gap_count,
                    severity=severity,
                    affected_project_ids=list(affected_projects_by_cap.get(cap, set())),
                )
                saved_gap = await self.workforce_repo.save_capability_gap(gap)
                gaps.append(saved_gap)

                if self.outbox_repo:
                    evt = CapabilityGapDetectedEvent(
                        gap_id=saved_gap.id,
                        capability=saved_gap.capability,
                        required_count=saved_gap.required_count,
                        available_count=saved_gap.available_count,
                        gap_count=saved_gap.gap_count,
                        severity=saved_gap.severity.value,
                    )
                    await self.outbox_repo.save_event(evt)

        return gaps

    async def generate_staffing_recommendation(
        self,
        demand: WorkforceDemand,
        all_employees: list[Employee],
        snapshots_by_emp: dict[str, float] | None = None,
        reliability_scores_by_emp: dict[str, float] | None = None,
    ) -> StaffingRecommendation:
        """
        Generates explainable, deterministic staffing recommendation for a demand.
        Scores candidate employees based on:
        Capability Fit (30%) + Availability (30%) + Workload Fit (20%) + Reliability (20%) - Penalty
        """
        snap_map = snapshots_by_emp or {}
        rel_map = reliability_scores_by_emp or {}

        # 1. Filter eligible candidates using EmployeeSelector
        eligible = self.employee_selector.find_eligible_employees(
            employees=all_employees,
            required_capabilities=[demand.capability],
            require_all=True,
        )

        candidates_with_scores: list[tuple[Employee, float, dict[str, Any]]] = []

        for emp in eligible:
            avail = snap_map.get(emp.id, 1.0)
            rel = rel_map.get(emp.id, 1.0)

            emp_caps = [c.name if hasattr(c, "name") else str(c) for c in emp.capabilities]
            cap_score = 1.0 if demand.capability in emp_caps else 0.7
            avail_score = min(1.0, max(0.0, avail))
            workload_score = 1.0 if avail >= 0.5 else (avail / 0.5)
            rel_score = min(1.0, max(0.0, rel))

            # Penalty for low availability
            penalty = 0.3 if avail < 0.2 else 0.0

            final_score = (
                (cap_score * 0.30)
                + (avail_score * 0.30)
                + (workload_score * 0.20)
                + (rel_score * 0.20)
                - penalty
            )
            final_score = round(max(0.0, min(1.0, final_score)), 2)

            details = {
                "cap_score": cap_score,
                "avail_score": avail_score,
                "workload_score": workload_score,
                "rel_score": rel_score,
                "penalty": penalty,
            }
            candidates_with_scores.append((emp, final_score, details))

        # Sort candidates descending by score
        candidates_with_scores.sort(key=lambda x: x[1], reverse=True)

        selected_cands = candidates_with_scores[: demand.required_count]
        cand_ids = [c[0].id for c in selected_cands]

        avg_score = (
            sum(c[1] for c in selected_cands) / len(selected_cands) if selected_cands else 0.0
        )

        reason_lines = [
            f"Demand requirement: {demand.required_count} x {demand.capability}.",
            f"Found {len(eligible)} eligible candidate(s).",
        ]
        for c, sc, dt in selected_cands:
            reason_lines.append(
                f"Candidate {c.name} ({c.id}): score={sc} [Cap={dt['cap_score']}, Avail={dt['avail_score']}, Workload={dt['workload_score']}, Rel={dt['rel_score']}]"
            )

        if len(selected_cands) < demand.required_count:
            reason_lines.append(
                f"WARNING: Capability gap remaining! Requested {demand.required_count}, matched {len(selected_cands)}."
            )

        rec = StaffingRecommendation(
            demand_id=demand.id,
            candidate_employee_ids=cand_ids,
            capability_fit_score=round(sum(c[2]["cap_score"] for c in selected_cands) / len(selected_cands), 2) if selected_cands else 0.0,
            availability_score=round(sum(c[2]["avail_score"] for c in selected_cands) / len(selected_cands), 2) if selected_cands else 0.0,
            workload_score=round(sum(c[2]["workload_score"] for c in selected_cands) / len(selected_cands), 2) if selected_cands else 0.0,
            reliability_score=round(sum(c[2]["rel_score"] for c in selected_cands) / len(selected_cands), 2) if selected_cands else 0.0,
            final_score=avg_score,
            reasoning="\n".join(reason_lines),
        )

        saved = await self.workforce_repo.save_recommendation(rec)

        if self.outbox_repo:
            evt = StaffingRecommendationCreatedEvent(
                recommendation_id=saved.id,
                demand_id=saved.demand_id,
                candidate_count=len(saved.candidate_employee_ids),
                final_score=saved.final_score,
            )
            await self.outbox_repo.save_event(evt)

        return saved

    async def create_workforce_plan(
        self,
        planning_horizon: str,
        objectives: list[str],
        demands: list[WorkforceDemand],
        gaps: list[CapabilityGap],
        recommendations: list[StaffingRecommendation],
    ) -> WorkforcePlan:
        plan = WorkforcePlan(
            planning_horizon=planning_horizon,
            objectives=objectives,
            demand_ids=[d.id for d in demands],
            gap_ids=[g.id for g in gaps],
            recommendation_ids=[r.id for r in recommendations],
            status=StaffingPlanStatus.DRAFT,
        )
        saved = await self.workforce_repo.save_plan(plan)

        if self.outbox_repo:
            evt = StaffingPlanCreatedEvent(
                plan_id=saved.id,
                planning_horizon=saved.planning_horizon,
                status=saved.status.value,
            )
            await self.outbox_repo.save_event(evt)

        return saved
