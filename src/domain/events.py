"""
Domain Events for Autonomous AI Organization Platform.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.employee import EmployeeStatus


@dataclass(frozen=True)
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class EmployeeCreatedEvent(DomainEvent):
    employee_id: str = ""
    employee_code: str = ""
    name: str = ""
    title: str = ""
    role: str = ""
    agent_id: str = ""
    department_id: str | None = None
    manager_id: str | None = None


@dataclass(frozen=True)
class EmployeeStatusChangedEvent(DomainEvent):
    employee_id: str = ""
    previous_status: EmployeeStatus = EmployeeStatus.INACTIVE
    new_status: EmployeeStatus = EmployeeStatus.ACTIVE
    reason: str | None = None


@dataclass(frozen=True)
class EmployeeManagerAssignedEvent(DomainEvent):
    employee_id: str = ""
    previous_manager_id: str | None = None
    new_manager_id: str | None = None


@dataclass(frozen=True)
class EmployeeDepartmentAssignedEvent(DomainEvent):
    employee_id: str = ""
    previous_department_id: str | None = None
    new_department_id: str | None = None


@dataclass(frozen=True)
class EmployeeWorkExecutedEvent(DomainEvent):
    employee_id: str = ""
    agent_id: str = ""
    run_id: str = ""
    objective: str = ""
    success: bool = True


@dataclass(frozen=True)
class ObjectiveCreatedEvent(DomainEvent):
    objective_id: str = ""
    title: str = ""
    requester: str = ""
    manager_id: str | None = None


@dataclass(frozen=True)
class ObjectiveClarificationRequestedEvent(DomainEvent):
    objective_id: str = ""
    questions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ObjectiveClarifiedEvent(DomainEvent):
    objective_id: str = ""
    answers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanCreatedEvent(DomainEvent):
    plan_id: str = ""
    objective_id: str = ""
    manager_id: str = ""
    work_item_count: int = 0


@dataclass(frozen=True)
class PlanApprovedEvent(DomainEvent):
    plan_id: str = ""
    objective_id: str = ""
    approved_by: str = ""


@dataclass(frozen=True)
class WorkItemCreatedEvent(DomainEvent):
    work_item_id: str = ""
    plan_id: str = ""
    title: str = ""


@dataclass(frozen=True)
class WorkItemAssignedEvent(DomainEvent):
    work_item_id: str = ""
    employee_id: str = ""
    assigned_by: str = ""


@dataclass(frozen=True)
class WorkItemReassignedEvent(DomainEvent):
    work_item_id: str = ""
    previous_employee_id: str | None = None
    new_employee_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class BlockerDetectedEvent(DomainEvent):
    work_item_id: str = ""
    objective_id: str = ""
    employee_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class WorkItemEscalatedEvent(DomainEvent):
    work_item_id: str = ""
    objective_id: str = ""
    escalated_by: str = ""
    escalated_to: str = ""
    reason: str = ""


@dataclass(frozen=True)
class ManagerDecisionCreatedEvent(DomainEvent):
    decision_id: str = ""
    manager_id: str = ""
    objective_id: str = ""
    decision_type: str = ""


@dataclass(frozen=True)
class ObjectiveCompletedEvent(DomainEvent):
    objective_id: str = ""
    manager_id: str | None = None
