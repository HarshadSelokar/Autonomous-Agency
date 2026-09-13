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


# Phase 4 Task Engine Events
@dataclass(frozen=True)
class TaskCreatedEvent(DomainEvent):
    task_id: str = ""
    plan_id: str = ""
    title: str = ""


@dataclass(frozen=True)
class TaskStatusChangedEvent(DomainEvent):
    task_id: str = ""
    previous_status: str = ""
    new_status: str = ""
    reason: str | None = None


@dataclass(frozen=True)
class TaskDependencyAddedEvent(DomainEvent):
    dependency_id: str = ""
    predecessor_task_id: str = ""
    successor_task_id: str = ""
    dependency_type: str = "BLOCKING"


@dataclass(frozen=True)
class TaskDependencyRemovedEvent(DomainEvent):
    dependency_id: str = ""
    predecessor_task_id: str = ""
    successor_task_id: str = ""


@dataclass(frozen=True)
class TaskBlockedEvent(DomainEvent):
    task_id: str = ""
    block_reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TaskReadyEvent(DomainEvent):
    task_id: str = ""


@dataclass(frozen=True)
class TaskAssignedEvent(DomainEvent):
    task_id: str = ""
    employee_id: str = ""
    assignment_id: str = ""


@dataclass(frozen=True)
class TaskExecutionStartedEvent(DomainEvent):
    task_id: str = ""
    employee_id: str = ""
    execution_run_id: str = ""


@dataclass(frozen=True)
class TaskExecutionFailedEvent(DomainEvent):
    task_id: str = ""
    execution_run_id: str = ""
    error: str = ""


@dataclass(frozen=True)
class TaskReviewRequestedEvent(DomainEvent):
    task_id: str = ""
    execution_run_id: str = ""


@dataclass(frozen=True)
class TaskReworkRequestedEvent(DomainEvent):
    task_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class TaskApprovedEvent(DomainEvent):
    task_id: str = ""
    approved_by: str = ""


@dataclass(frozen=True)
class TaskCompletedEvent(DomainEvent):
    task_id: str = ""


@dataclass(frozen=True)
class TaskFailedEvent(DomainEvent):
    task_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class TaskCancelledEvent(DomainEvent):
    task_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class TaskRetryScheduledEvent(DomainEvent):
    task_id: str = ""
    retry_count: int = 0
    max_retries: int = 3


# Phase 5 Communication Domain Events
@dataclass(frozen=True)
class ConversationCreatedEvent(DomainEvent):
    conversation_id: str = ""
    conversation_type: str = ""
    created_by_employee_id: str = ""


@dataclass(frozen=True)
class ConversationParticipantAddedEvent(DomainEvent):
    conversation_id: str = ""
    participant_id: str = ""
    participant_type: str = "employee"


@dataclass(frozen=True)
class ConversationParticipantRemovedEvent(DomainEvent):
    conversation_id: str = ""
    participant_id: str = ""


@dataclass(frozen=True)
class MessageCreatedEvent(DomainEvent):
    message_id: str = ""
    conversation_id: str = ""
    sender_employee_id: str = ""
    message_type: str = ""


@dataclass(frozen=True)
class MessageDeliveredEvent(DomainEvent):
    message_id: str = ""
    conversation_id: str = ""
    delivered_to_employee_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MessageReadEvent(DomainEvent):
    message_id: str = ""
    read_by_employee_id: str = ""


@dataclass(frozen=True)
class MessageAcknowledgedEvent(DomainEvent):
    message_id: str = ""
    acknowledged_by_employee_id: str = ""
    timestamp: str = ""


@dataclass(frozen=True)
class MessageDeliveryFailedEvent(DomainEvent):
    message_id: str = ""
    recipient_employee_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class DecisionProposedEvent(DomainEvent):
    decision_id: str = ""
    title: str = ""
    proposer_employee_id: str = ""
    provenance: str = ""


@dataclass(frozen=True)
class DecisionApprovedEvent(DomainEvent):
    decision_id: str = ""
    title: str = ""
    approver_employee_id: str = ""
    chosen_option: str | None = None
    meeting_id: str | None = None
    task_id: str | None = None
    objective_id: str | None = None


@dataclass(frozen=True)
class DecisionRejectedEvent(DomainEvent):
    decision_id: str = ""
    approver_employee_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class DecisionSupersededEvent(DomainEvent):
    old_decision_id: str = ""
    new_decision_id: str = ""
    actor_employee_id: str = ""


@dataclass(frozen=True)
class MeetingStartedEvent(DomainEvent):
    meeting_id: str = ""
    actual_start: str = ""


@dataclass(frozen=True)
class MeetingEndedEvent(DomainEvent):
    meeting_id: str = ""
    actual_end: str = ""


# Phase 8 Tool & Integration Events
@dataclass(frozen=True)
class ToolExecutionRequestedEvent(DomainEvent):
    execution_id: str = ""
    tool_id: str = ""
    capability: str = ""
    employee_id: str = ""
    agent_id: str = ""


@dataclass(frozen=True)
class ToolExecutionApprovedEvent(DomainEvent):
    execution_id: str = ""
    approval_id: str = ""
    approver_employee_id: str = ""


@dataclass(frozen=True)
class ToolExecutionDeniedEvent(DomainEvent):
    execution_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class ToolExecutionSucceededEvent(DomainEvent):
    execution_id: str = ""
    tool_id: str = ""
    evidence_id: str | None = None


@dataclass(frozen=True)
class ToolExecutionFailedEvent(DomainEvent):
    execution_id: str = ""
    tool_id: str = ""
    error_message: str = ""


