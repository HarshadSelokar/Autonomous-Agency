"""
Pydantic schemas for Plan, WorkItem, Assignment, and Decision API endpoints.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.domain.assignment import Assignment, AssignmentStatus
from src.domain.decision import DecisionType, ManagerDecision
from src.domain.plan import Plan, PlanStatus
from src.domain.work_item import WorkItem, WorkItemStatus


class WorkItemSchema(BaseModel):
    id: str
    title: str
    description: str
    required_capabilities: list[str] = Field(default_factory=list)
    priority: str = "medium"

    def to_domain(self, plan_id: str) -> WorkItem:
        return WorkItem(
            id=self.id,
            plan_id=plan_id,
            title=self.title,
            description=self.description,
            required_capabilities=self.required_capabilities,
            priority=self.priority,
        )


class SubmitPlanRequest(BaseModel):
    id: str
    objective_id: str
    manager_id: str
    assumptions: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    work_items: list[WorkItemSchema] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssignWorkItemRequest(BaseModel):
    employee_id: str
    assigned_by_manager_id: str
    reason: str = ""


class ReassignWorkItemRequest(BaseModel):
    new_employee_id: str
    assigned_by_manager_id: str
    reason: str


class HandleBlockerRequest(BaseModel):
    work_item_id: str
    employee_id: str
    reason: str


class EscalateWorkItemRequest(BaseModel):
    work_item_id: str
    manager_id: str
    reason: str


class WorkItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    plan_id: str
    title: str
    description: str
    required_capabilities: list[str]
    priority: str
    assigned_employee_id: str | None
    status: WorkItemStatus
    result: dict[str, Any] | None
    blocker_reason: str | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, wi: WorkItem) -> "WorkItemResponse":
        return cls(
            id=wi.id,
            plan_id=wi.plan_id,
            title=wi.title,
            description=wi.description,
            required_capabilities=wi.required_capabilities,
            priority=wi.priority,
            assigned_employee_id=wi.assigned_employee_id,
            status=wi.status,
            result=wi.result,
            blocker_reason=wi.blocker_reason,
            metadata=wi.metadata,
            created_at=wi.created_at,
            updated_at=wi.updated_at,
        )


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    objective_id: str
    manager_id: str
    assumptions: list[str]
    goals: list[str]
    work_items: list[WorkItemResponse]
    required_capabilities: list[str]
    risks: list[str]
    constraints: list[str]
    status: PlanStatus
    version: int
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, plan: Plan) -> "PlanResponse":
        return cls(
            id=plan.id,
            objective_id=plan.objective_id,
            manager_id=plan.manager_id,
            assumptions=plan.assumptions,
            goals=plan.goals,
            work_items=[WorkItemResponse.from_domain(w) for w in plan.work_items],
            required_capabilities=plan.required_capabilities,
            risks=plan.risks,
            constraints=plan.constraints,
            status=plan.status,
            version=plan.version,
            metadata=plan.metadata,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    work_item_id: str
    employee_id: str
    assigned_by: str
    reason: str
    status: AssignmentStatus
    metadata: dict[str, Any]
    assigned_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, asgn: Assignment) -> "AssignmentResponse":
        return cls(
            id=asgn.id,
            work_item_id=asgn.work_item_id,
            employee_id=asgn.employee_id,
            assigned_by=asgn.assigned_by,
            reason=asgn.reason,
            status=asgn.status,
            metadata=asgn.metadata,
            assigned_at=asgn.assigned_at,
            updated_at=asgn.updated_at,
        )


class DecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    manager_id: str
    objective_id: str
    decision_type: DecisionType
    reasoning_summary: str
    selected_action: str
    alternatives: list[str]
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def from_domain(cls, dec: ManagerDecision) -> "DecisionResponse":
        return cls(
            id=dec.id,
            manager_id=dec.manager_id,
            objective_id=dec.objective_id,
            decision_type=dec.decision_type,
            reasoning_summary=dec.reasoning_summary,
            selected_action=dec.selected_action,
            alternatives=dec.alternatives,
            metadata=dec.metadata,
            created_at=dec.created_at,
        )
