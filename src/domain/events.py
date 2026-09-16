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


# Phase 9 AI Software Company Events
@dataclass(frozen=True)
class SoftwareProjectCreatedEvent(DomainEvent):
    project_id: str = ""
    objective_id: str = ""
    name: str = ""
    repository_path: str = ""


@dataclass(frozen=True)
class SoftwareRequirementCreatedEvent(DomainEvent):
    requirement_id: str = ""
    project_id: str = ""
    title: str = ""
    priority: str = "MEDIUM"


@dataclass(frozen=True)
class EngineeringPlanCreatedEvent(DomainEvent):
    plan_id: str = ""
    project_id: str = ""
    manager_employee_id: str = ""
    task_count: int = 0


@dataclass(frozen=True)
class CodeChangeCreatedEvent(DomainEvent):
    change_id: str = ""
    project_id: str = ""
    task_id: str = ""
    author_employee_id: str = ""
    branch_name: str = ""


@dataclass(frozen=True)
class CodeReviewRequestedEvent(DomainEvent):
    review_id: str = ""
    change_id: str = ""
    reviewer_employee_id: str = ""


@dataclass(frozen=True)
class CodeReviewApprovedEvent(DomainEvent):
    review_id: str = ""
    change_id: str = ""
    reviewer_employee_id: str = ""


@dataclass(frozen=True)
class CodeReviewChangesRequestedEvent(DomainEvent):
    review_id: str = ""
    change_id: str = ""
    reviewer_employee_id: str = ""
    findings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TestRunStartedEvent(DomainEvent):
    test_run_id: str = ""
    task_id: str = ""
    workspace_id: str = ""
    command: str = ""


@dataclass(frozen=True)
class TestRunSucceededEvent(DomainEvent):
    test_run_id: str = ""
    task_id: str = ""
    passed_count: int = 0


@dataclass(frozen=True)
class TestRunFailedEvent(DomainEvent):
    test_run_id: str = ""
    task_id: str = ""
    failed_count: int = 0
    error_summary: str = ""


@dataclass(frozen=True)
class SoftwareDefectCreatedEvent(DomainEvent):
    defect_id: str = ""
    project_id: str = ""
    title: str = ""
    severity: str = "MEDIUM"
    originating_task_id: str | None = None


@dataclass(frozen=True)
class SoftwareDefectFixedEvent(DomainEvent):
    defect_id: str = ""
    fix_task_id: str = ""


@dataclass(frozen=True)
class SoftwareDeliveryApprovedEvent(DomainEvent):
    delivery_id: str = ""
    project_id: str = ""
    approved_by_employee_id: str = ""


@dataclass(frozen=True)
class SoftwareDeliveredEvent(DomainEvent):
    delivery_id: str = ""
    project_id: str = ""
    version: str = ""
    commit_hash: str = ""


# Phase 10 Verification & Recovery Events
@dataclass(frozen=True)
class VerificationRequestedEvent(DomainEvent):
    verification_id: str = ""
    task_id: str = ""
    outcome_id: str = ""


@dataclass(frozen=True)
class VerificationStartedEvent(DomainEvent):
    verification_id: str = ""
    task_id: str = ""


@dataclass(frozen=True)
class VerificationPassedEvent(DomainEvent):
    verification_id: str = ""
    task_id: str = ""
    evidence_count: int = 0


@dataclass(frozen=True)
class VerificationFailedEvent(DomainEvent):
    verification_id: str = ""
    task_id: str = ""
    failed_check_count: int = 0
    recommended_recovery: str = ""


@dataclass(frozen=True)
class VerificationInconclusiveEvent(DomainEvent):
    verification_id: str = ""
    task_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class RecoveryRequestedEvent(DomainEvent):
    recovery_action_id: str = ""
    failure_id: str = ""
    task_id: str = ""
    strategy: str = ""


@dataclass(frozen=True)
class RecoveryStartedEvent(DomainEvent):
    recovery_action_id: str = ""
    task_id: str = ""
    strategy: str = ""


@dataclass(frozen=True)
class RecoverySucceededEvent(DomainEvent):
    recovery_action_id: str = ""
    task_id: str = ""
    strategy: str = ""


@dataclass(frozen=True)
class RecoveryFailedEvent(DomainEvent):
    recovery_action_id: str = ""
    task_id: str = ""
    strategy: str = ""
    reason: str = ""


@dataclass(frozen=True)
class HumanVerificationRequestedEvent(DomainEvent):
    verification_id: str = ""
    task_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class HumanVerificationApprovedEvent(DomainEvent):
    verification_id: str = ""
    task_id: str = ""
    approved_by_actor_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class HumanVerificationRejectedEvent(DomainEvent):
    verification_id: str = ""
    task_id: str = ""
    rejected_by_actor_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class TaskReassignedEvent(DomainEvent):
    task_id: str = ""
    previous_employee_id: str | None = None
    new_employee_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class TaskEscalatedEvent(DomainEvent):
    task_id: str = ""
    objective_id: str = ""
    escalated_by: str = ""
    escalated_to: str = ""
    reason: str = ""


# Phase 11 Human Governance Events
@dataclass(frozen=True)
class GovernancePolicyCreatedEvent(DomainEvent):
    policy_id: str = ""
    name: str = ""
    level: str = ""


@dataclass(frozen=True)
class ApprovalRequestedEvent(DomainEvent):
    request_id: str = ""
    action_type: str = ""
    requested_by_actor_id: str = ""
    risk_level: str = ""


@dataclass(frozen=True)
class ApprovalGrantedEvent(DomainEvent):
    request_id: str = ""
    approved_by_actor_id: str = ""


@dataclass(frozen=True)
class ApprovalRejectedEvent(DomainEvent):
    request_id: str = ""
    rejected_by_actor_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class ApprovalExpiredEvent(DomainEvent):
    request_id: str = ""


@dataclass(frozen=True)
class AutonomyPausedEvent(DomainEvent):
    scope: str = ""
    scope_id: str = ""
    paused_by_actor_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class AutonomyResumedEvent(DomainEvent):
    scope: str = ""
    scope_id: str = ""
    resumed_by_actor_id: str = ""


@dataclass(frozen=True)
class EmergencyStopActivatedEvent(DomainEvent):
    stop_id: str = ""
    scope: str = ""
    scope_id: str = ""
    activated_by_actor_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class GovernanceViolationDetectedEvent(DomainEvent):
    violation_id: str = ""
    category: str = ""
    actor_id: str = ""
    severity: str = ""


@dataclass(frozen=True)
class GovernanceOverrideAppliedEvent(DomainEvent):
    override_id: str = ""
    action_id: str = ""
    actor_id: str = ""
    reason: str = ""


# Phase 12 Model Routing Events
@dataclass(frozen=True)
class ModelSelectionRequestedEvent(DomainEvent):
    request_id: str = ""
    task_id: str | None = None
    strategy: str = ""


@dataclass(frozen=True)
class ModelSelectedEvent(DomainEvent):
    decision_id: str = ""
    selected_model_id: str = ""
    provider_name: str = ""
    is_fallback: bool = False


@dataclass(frozen=True)
class ModelFallbackUsedEvent(DomainEvent):
    decision_id: str = ""
    primary_model_id: str = ""
    fallback_model_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class ModelUnavailableEvent(DomainEvent):
    model_id: str = ""
    provider_name: str = ""
    reason: str = ""


@dataclass(frozen=True)
class ModelHealthChangedEvent(DomainEvent):
    model_id: str = ""
    provider_name: str = ""
    is_healthy: bool = True


# Phase 13 Pixel Office Events
@dataclass(frozen=True)
class OfficeStateUpdatedEvent(DomainEvent):
    employee_id: str = ""
    visual_state: str = ""
    activity_summary: str = ""
    task_id: str | None = None
    project_id: str | None = None


# Phase 14 Department Events
@dataclass(frozen=True)
class DepartmentCreatedEvent(DomainEvent):
    department_id: str = ""
    name: str = ""
    code: str = ""


@dataclass(frozen=True)
class DepartmentStatusChangedEvent(DomainEvent):
    department_id: str = ""
    previous_status: str = ""
    new_status: str = ""
    reason: str | None = None


@dataclass(frozen=True)
class DepartmentManagerAssignedEvent(DomainEvent):
    department_id: str = ""
    manager_employee_id: str = ""


@dataclass(frozen=True)
class DepartmentRequestCreatedEvent(DomainEvent):
    request_id: str = ""
    requester_department_id: str = ""
    receiving_department_id: str = ""
    purpose: str = ""


@dataclass(frozen=True)
class DepartmentRequestAcceptedEvent(DomainEvent):
    request_id: str = ""
    receiving_manager_id: str = ""
    delivery_owner_employee_id: str = ""


@dataclass(frozen=True)
class DepartmentRequestRejectedEvent(DomainEvent):
    request_id: str = ""
    receiving_manager_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class DepartmentRequestDeliveredEvent(DomainEvent):
    request_id: str = ""
    delivery_owner_employee_id: str = ""


@dataclass(frozen=True)
class DepartmentRequestVerifiedEvent(DomainEvent):
    request_id: str = ""
    verified_by_employee_id: str = ""
    success: bool = True


@dataclass(frozen=True)
class DepartmentHandoffCreatedEvent(DomainEvent):
    handoff_id: str = ""
    request_id: str = ""
    sender_department_id: str = ""
    receiver_department_id: str = ""


@dataclass(frozen=True)
class DepartmentHandoffAcceptedEvent(DomainEvent):
    handoff_id: str = ""
    receiver_employee_id: str = ""


@dataclass(frozen=True)
class DepartmentHandoffRejectedEvent(DomainEvent):
    handoff_id: str = ""
    receiver_employee_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class DepartmentEscalatedEvent(DomainEvent):
    department_id: str = ""
    request_id: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class DepartmentHealthChangedEvent(DomainEvent):
    department_id: str = ""
    previous_health: str = ""
    new_health: str = ""
    reason: str = ""


# Phase 15 Dynamic Workforce Events

@dataclass(frozen=True)
class WorkforceDemandCreatedEvent(DomainEvent):
    demand_id: str = ""
    source_type: str = ""
    source_id: str = ""
    capability: str = ""
    required_count: int = 1


@dataclass(frozen=True)
class CapabilityGapDetectedEvent(DomainEvent):
    gap_id: str = ""
    capability: str = ""
    required_count: int = 0
    available_count: int = 0
    gap_count: int = 0
    severity: str = "LOW"


@dataclass(frozen=True)
class StaffingPlanCreatedEvent(DomainEvent):
    plan_id: str = ""
    planning_horizon: str = ""
    status: str = "DRAFT"


@dataclass(frozen=True)
class StaffingRecommendationCreatedEvent(DomainEvent):
    recommendation_id: str = ""
    demand_id: str = ""
    candidate_count: int = 0
    final_score: float = 0.0


@dataclass(frozen=True)
class StaffingRecommendationAcceptedEvent(DomainEvent):
    recommendation_id: str = ""
    accepted_by_id: str = ""


@dataclass(frozen=True)
class StaffingRecommendationRejectedEvent(DomainEvent):
    recommendation_id: str = ""
    rejected_by_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class TeamFormationRequestedEvent(DomainEvent):
    request_id: str = ""
    team_name: str = ""
    requested_by_id: str = ""


@dataclass(frozen=True)
class TeamFormedEvent(DomainEvent):
    team_id: str = ""
    team_name: str = ""
    team_type: str = ""
    manager_id: str | None = None
    member_count: int = 0


@dataclass(frozen=True)
class TeamMemberAddedEvent(DomainEvent):
    team_id: str = ""
    employee_id: str = ""
    role_in_team: str = "MEMBER"
    allocation_percentage: float = 100.0


@dataclass(frozen=True)
class TeamMemberRemovedEvent(DomainEvent):
    team_id: str = ""
    employee_id: str = ""


@dataclass(frozen=True)
class TeamPausedEvent(DomainEvent):
    team_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class TeamDissolvedEvent(DomainEvent):
    team_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class EmployeeReallocatedEvent(DomainEvent):
    allocation_id: str = ""
    employee_id: str = ""
    team_id: str | None = None
    allocation_percentage: float = 100.0


@dataclass(frozen=True)
class WorkforceChangeRequestedEvent(DomainEvent):
    request_id: str = ""
    request_type: str = ""
    target_id: str = ""
    requested_by_id: str = ""


@dataclass(frozen=True)
class WorkforceDecisionMadeEvent(DomainEvent):
    decision_id: str = ""
    change_request_id: str | None = None
    actor_id: str = ""
    decision_type: str = "APPROVED"


@dataclass(frozen=True)
class WorkforceEscalatedEvent(DomainEvent):
    gap_id: str = ""
    reason: str = ""


# Phase 16 Autonomous Company Events

@dataclass(frozen=True)
class CompanyOperatingCycleStartedEvent(DomainEvent):
    cycle_id: str = ""
    company_id: str = ""
    cycle_number: int = 1
    initiated_by_id: str = "system"


@dataclass(frozen=True)
class CompanyOperatingCycleStateChangedEvent(DomainEvent):
    cycle_id: str = ""
    company_id: str = ""
    previous_state: str = ""
    new_state: str = ""


@dataclass(frozen=True)
class CompanyHealthEvaluatedEvent(DomainEvent):
    snapshot_id: str = ""
    company_id: str = ""
    health_snapshot_id: str = ""
    overall_status: str = "HEALTHY"
    explanation: str = ""


@dataclass(frozen=True)
class StrategyProposedEvent(DomainEvent):
    proposal_id: str = ""
    company_id: str = ""
    proposal_type: str = ""
    proposed_by_id: str = ""


@dataclass(frozen=True)
class StrategyApprovedEvent(DomainEvent):
    proposal_id: str = ""
    company_id: str = ""
    approved_by_id: str = ""


@dataclass(frozen=True)
class StrategyRolledBackEvent(DomainEvent):
    company_id: str = ""
    previous_version: int = 1
    new_version: int = 1
    reason: str = ""


@dataclass(frozen=True)
class CompanyRiskDetectedEvent(DomainEvent):
    risk_id: str = ""
    company_id: str = ""
    title: str = ""
    severity: str = "LOW"


@dataclass(frozen=True)
class CompanyOpportunityDetectedEvent(DomainEvent):
    opportunity_id: str = ""
    company_id: str = ""
    title: str = ""
    expected_value: float = 0.0


@dataclass(frozen=True)
class ContinuousImprovementProposedEvent(DomainEvent):
    proposal_id: str = ""
    company_id: str = ""
    title: str = ""


@dataclass(frozen=True)
class StrategySimulationExecutedEvent(DomainEvent):
    simulation_id: str = ""
    company_id: str = ""
    title: str = ""


@dataclass(frozen=True)
class CompanyObservationCompletedEvent(DomainEvent):
    company_id: str = ""
    cycle_id: str = ""
    fact_count: int = 0
    health_status: str = ""


@dataclass(frozen=True)
class CompanyRiskIdentifiedEvent(DomainEvent):
    company_id: str = ""
    risk_id: str = ""
    title: str = ""
    severity: str = ""


@dataclass(frozen=True)
class StrategicAnalysisCompletedEvent(DomainEvent):
    company_id: str = ""
    cycle_id: str = ""
    analysis_id: str = ""
    confidence: float = 1.0
    model_used: str = ""


@dataclass(frozen=True)
class StrategyProposalCreatedEvent(DomainEvent):
    company_id: str = ""
    proposal_id: str = ""
    proposal_type: str = ""
    title: str = ""
    governance_level: str = ""


@dataclass(frozen=True)
class StrategySimulationCreatedEvent(DomainEvent):
    company_id: str = ""
    simulation_id: str = ""
    title: str = ""
    is_authoritative: bool = False


@dataclass(frozen=True)
class CompanyOperatingCyclePhaseTransitionedEvent(DomainEvent):
    company_id: str = ""
    cycle_id: str = ""
    from_state: str = ""
    to_state: str = ""


@dataclass(frozen=True)
class CompanyOperatingCycleCompletedEvent(DomainEvent):
    company_id: str = ""
    cycle_id: str = ""
    cycle_number: int = 1
    summary: str = ""


@dataclass(frozen=True)
class CompanyOperatingCycleFailedEvent(DomainEvent):
    company_id: str = ""
    cycle_id: str = ""
    failure_reason: str = ""


@dataclass(frozen=True)
class CompanyOperatingCyclePausedEvent(DomainEvent):
    company_id: str = ""
    cycle_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class CompanyOperatingCycleResumedEvent(DomainEvent):
    company_id: str = ""
    cycle_id: str = ""
    resumed_state: str = ""


@dataclass(frozen=True)
class ExecutiveReportGeneratedEvent(DomainEvent):
    company_id: str = ""
    report_id: str = ""
    health_status: str = ""
    open_risks_count: int = 0


@dataclass(frozen=True)
class PortfolioItemUpdatedEvent(DomainEvent):
    company_id: str = ""
    portfolio_item_id: str = ""
    progress_pct: float = 0.0
    has_bottleneck: bool = False


@dataclass(frozen=True)
class ResourceAllocationPlanApprovedEvent(DomainEvent):
    company_id: str = ""
    plan_id: str = ""
    approved_by_id: str = ""


@dataclass(frozen=True)
class ContinuousImprovementProposalSubmittedEvent(DomainEvent):
    company_id: str = ""
    proposal_id: str = ""
    title: str = ""
    governance_required: bool = True


# Phase 18 Institutional Knowledge & Learning Events

@dataclass(frozen=True)
class KnowledgeCandidateDiscoveredEvent(DomainEvent):
    knowledge_id: str = ""
    statement: str = ""
    knowledge_type: str = "FACT"
    scope: str = "COMPANY"


@dataclass(frozen=True)
class KnowledgeValidatedEvent(DomainEvent):
    knowledge_id: str = ""
    validator_id: str = ""
    validation_status: str = "PASSED"


@dataclass(frozen=True)
class KnowledgeAuthorityPromotedEvent(DomainEvent):
    knowledge_id: str = ""
    old_authority: str = ""
    new_authority: str = ""


@dataclass(frozen=True)
class KnowledgeConflictDetectedEvent(DomainEvent):
    conflict_id: str = ""
    knowledge_id_a: str = ""
    knowledge_id_b: str = ""


@dataclass(frozen=True)
class KnowledgeConflictResolvedEvent(DomainEvent):
    conflict_id: str = ""
    resolution_strategy: str = ""


@dataclass(frozen=True)
class KnowledgeMarkedStaleEvent(DomainEvent):
    knowledge_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class KnowledgeProcedureProposedEvent(DomainEvent):
    procedure_id: str = ""
    title: str = ""
    version: int = 1


@dataclass(frozen=True)
class KnowledgeProcedureApprovedEvent(DomainEvent):
    procedure_id: str = ""
    governance_approval_id: str = ""


@dataclass(frozen=True)
class OrganizationalExperimentStartedEvent(DomainEvent):
    experiment_id: str = ""
    title: str = ""


@dataclass(frozen=True)
class OrganizationalExperimentCompletedEvent(DomainEvent):
    experiment_id: str = ""
    title: str = ""
    conclusion: str = ""


# Phase 22 — Swarm Domain Events
@dataclass(frozen=True)
class SwarmCreatedEvent(DomainEvent):
    swarm_id: str = ""
    code: str = ""
    parent_task_id: str = ""
    coordination_mode: str = ""


@dataclass(frozen=True)
class SwarmStartedEvent(DomainEvent):
    swarm_id: str = ""


@dataclass(frozen=True)
class SwarmPausedEvent(DomainEvent):
    swarm_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class SwarmResumedEvent(DomainEvent):
    swarm_id: str = ""


@dataclass(frozen=True)
class SwarmCompletedEvent(DomainEvent):
    swarm_id: str = ""
    result_id: str = ""


@dataclass(frozen=True)
class SwarmFailedEvent(DomainEvent):
    swarm_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class SwarmCancelledEvent(DomainEvent):
    swarm_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class SwarmMemberJoinedEvent(DomainEvent):
    swarm_id: str = ""
    member_id: str = ""
    employee_id: str = ""
    role: str = ""


@dataclass(frozen=True)
class SwarmMemberRemovedEvent(DomainEvent):
    swarm_id: str = ""
    member_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class SwarmMemberFailedEvent(DomainEvent):
    swarm_id: str = ""
    member_id: str = ""
    reason: str = ""


@dataclass(frozen=True)
class SwarmMemberRecoveredEvent(DomainEvent):
    swarm_id: str = ""
    member_id: str = ""
    action: str = ""


@dataclass(frozen=True)
class SwarmTaskAssignedEvent(DomainEvent):
    swarm_id: str = ""
    member_id: str = ""
    task_id: str = ""


@dataclass(frozen=True)
class SwarmTaskCompletedEvent(DomainEvent):
    swarm_id: str = ""
    member_id: str = ""
    task_id: str = ""


@dataclass(frozen=True)
class SwarmResultProducedEvent(DomainEvent):
    swarm_id: str = ""
    result_id: str = ""


@dataclass(frozen=True)
class SwarmConflictDetectedEvent(DomainEvent):
    swarm_id: str = ""
    conflict_id: str = ""
    task_id: str = ""


@dataclass(frozen=True)
class SwarmVerificationStartedEvent(DomainEvent):
    swarm_id: str = ""
    verification_id: str = ""


@dataclass(frozen=True)
class SwarmVerificationCompletedEvent(DomainEvent):
    swarm_id: str = ""
    verification_id: str = ""
    status: str = ""


# Phase 23 Business Operations Events

@dataclass(frozen=True)
class BusinessTransactionRecordedEvent(DomainEvent):
    transaction_id: str = ""
    transaction_type: str = ""
    amount_cents: int = 0
    currency: str = "USD"
    account_id: str = ""
    counterparty: str = ""
    idempotency_key: str | None = None


@dataclass(frozen=True)
class RevenueRecordedEvent(DomainEvent):
    revenue_id: str = ""
    customer_id: str = ""
    amount_cents: int = 0
    currency: str = "USD"
    recognition_state: str = "EXPECTED"


@dataclass(frozen=True)
class ExpenseRecordedEvent(DomainEvent):
    expense_id: str = ""
    vendor_id: str = ""
    category: str = ""
    amount_cents: int = 0
    currency: str = "USD"
    department_id: str | None = None


@dataclass(frozen=True)
class InvoiceCreatedEvent(DomainEvent):
    invoice_id: str = ""
    invoice_number: str = ""
    customer_id: str = ""
    total_cents: int = 0
    currency: str = "USD"
    status: str = "DRAFT"


@dataclass(frozen=True)
class InvoiceIssuedEvent(DomainEvent):
    invoice_id: str = ""
    invoice_number: str = ""
    issued_by: str = ""


@dataclass(frozen=True)
class PaymentRecordedEvent(DomainEvent):
    payment_id: str = ""
    invoice_id: str | None = None
    amount_cents: int = 0
    currency: str = "USD"
    status: str = "EXPECTED"


@dataclass(frozen=True)
class SubscriptionRenewalDueEvent(DomainEvent):
    subscription_id: str = ""
    customer_id: str = ""
    amount_cents: int = 0
    renewal_date: str = ""


@dataclass(frozen=True)
class ProcurementRequestedEvent(DomainEvent):
    request_id: str = ""
    requester_id: str = ""
    item_description: str = ""
    estimated_cents: int = 0
    currency: str = "USD"


@dataclass(frozen=True)
class ProcurementApprovedEvent(DomainEvent):
    request_id: str = ""
    approved_by: str = ""
    purchase_order_id: str = ""


@dataclass(frozen=True)
class PurchaseOrderCreatedEvent(DomainEvent):
    purchase_order_id: str = ""
    vendor_id: str = ""
    total_cents: int = 0


@dataclass(frozen=True)
class BudgetExceededEvent(DomainEvent):
    budget_id: str = ""
    department_id: str | None = None
    allocated_cents: int = 0
    consumed_cents: int = 0
    requested_cents: int = 0


@dataclass(frozen=True)
class ReconciliationMismatchEvent(DomainEvent):
    reconciliation_id: str = ""
    internal_ref: str = ""
    external_ref: str = ""
    internal_cents: int = 0
    external_cents: int = 0


@dataclass(frozen=True)
class ReconciliationCompletedEvent(DomainEvent):
    reconciliation_id: str = ""
    status: str = "MATCHED"
    matched_count: int = 0
    mismatch_count: int = 0






