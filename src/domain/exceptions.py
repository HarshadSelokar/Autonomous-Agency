"""
Domain layer typed exceptions for Agent Runtime.
"""


class DomainError(Exception):
    """Base class for all domain-level errors."""

    pass


class InvalidStateTransitionError(DomainError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, entity: str, entity_id: str, current_state: str, target_state: str) -> None:
        self.entity = entity
        self.entity_id = entity_id
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(
            f"Invalid state transition for {entity} '{entity_id}': "
            f"cannot transition from '{current_state}' to '{target_state}'."
        )


class AgentNotFoundError(DomainError):
    """Raised when an agent is not found."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__(f"Agent with ID '{agent_id}' was not found.")


class AgentValidationError(DomainError):
    """Raised when agent data fails domain validation."""

    pass


class EmployeeNotFoundError(DomainError):
    """Raised when an employee is not found."""

    def __init__(self, employee_id: str) -> None:
        self.employee_id = employee_id
        super().__init__(f"Employee with ID '{employee_id}' was not found.")


class EmployeeValidationError(DomainError):
    """Raised when employee data fails domain validation."""

    pass


class ConfigurationError(DomainError):
    """Raised when application or agent configuration is invalid."""

    pass


class ProviderUnavailableError(DomainError):
    """Raised when model provider is unreachable or temporarily down."""

    pass


class AuthenticationError(DomainError):
    """Raised when provider authentication (API key) fails."""

    pass


class RateLimitError(DomainError):
    """Raised when provider rate limit is exceeded."""

    pass


class TimeoutError(DomainError):
    """Raised when model provider request times out."""

    pass


class ModelExecutionError(DomainError):
    """Raised when model provider returns an execution error."""

    pass


class InvalidResponseError(DomainError):
    """Raised when model response is invalid or malformed."""

    pass


class StructuredOutputValidationError(DomainError):
    """Raised when structured output validation fails."""

    pass


class ContextError(DomainError):
    """Raised when context construction fails."""

    pass


class CancellationError(DomainError):
    """Raised when an execution run is cancelled."""

    pass


class ObjectiveNotFoundError(DomainError):
    """Raised when an objective is not found."""

    def __init__(self, objective_id: str) -> None:
        self.objective_id = objective_id
        super().__init__(f"Objective with ID '{objective_id}' was not found.")


class ObjectiveValidationError(DomainError):
    """Raised when objective data fails domain validation."""

    pass


class PlanValidationError(DomainError):
    """Raised when plan structure or validation fails."""

    pass


class AssignmentError(DomainError):
    """Raised when work item assignment or reassignment fails."""

    pass


class EscalationError(DomainError):
    """Raised when work escalation fails."""

    pass


class TaskValidationError(DomainError):
    """Raised when task data fails domain validation."""

    pass


class TaskNotFoundError(DomainError):
    """Raised when a task is not found."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task with ID '{task_id}' was not found.")


class TaskDependencyError(DomainError):
    """Raised when task dependency validation or creation fails."""

    pass


class TaskCycleError(DomainError):
    """Raised when a task dependency cycle is detected."""

    pass


class TaskNotReadyError(DomainError):
    """Raised when attempting to execute a task that is not in READY state."""

    pass


class TaskClaimError(DomainError):
    """Raised when claiming a task fails due to concurrency or state conflict."""

    pass


class UnauthorizedApprovalError(DomainError):
    """Raised when an unauthorized approval (e.g. self-approval) is attempted."""

    pass


class SwarmNotFoundError(DomainError):
    """Raised when a swarm is not found."""

    def __init__(self, swarm_id: str) -> None:
        self.swarm_id = swarm_id
        super().__init__(f"Swarm with ID '{swarm_id}' was not found.")


class SwarmValidationError(DomainError):
    """Raised when swarm parameters or topology validation fails."""

    pass


class SwarmBudgetExceededError(DomainError):
    """Raised when a swarm breaches its allocated resource budget."""

    pass


class SwarmDepthExceededError(DomainError):
    """Raised when nested swarm creation exceeds maximum permitted depth."""

    pass


class SwarmGovernanceViolationError(DomainError):
    """Raised when a swarm operation violates governance policy."""

    pass


class SwarmConflictError(DomainError):
    """Raised when unresolvable agent result conflicts occur."""

    pass


class BusinessError(DomainError):
    """Base exception for all Business Operations domain errors."""

    pass


class MoneyArithmeticError(BusinessError):
    """Raised when monetary calculations involve mismatched currencies or invalid float inputs."""

    pass


class BudgetExceededError(BusinessError):
    """Raised when a requested business expenditure exceeds allocated budget bounds."""

    def __init__(self, budget_id: str, requested_cents: int, remaining_cents: int) -> None:
        self.budget_id = budget_id
        self.requested_cents = requested_cents
        self.remaining_cents = remaining_cents
        super().__init__(
            f"Budget '{budget_id}' exceeded: requested {requested_cents} cents, but only {remaining_cents} cents remaining."
        )


class FinancialPeriodClosedError(BusinessError):
    """Raised when an edit is attempted on a closed financial period without authorization."""

    def __init__(self, period_id: str) -> None:
        self.period_id = period_id
        super().__init__(f"Financial period '{period_id}' is closed to modifications.")


class ReconciliationMismatchError(BusinessError):
    """Raised when internal and external transaction records fail to reconcile deterministically."""

    def __init__(self, internal_ref: str, external_ref: str, detail: str) -> None:
        self.internal_ref = internal_ref
        self.external_ref = external_ref
        self.detail = detail
        super().__init__(
            f"Reconciliation mismatch between internal '{internal_ref}' and external '{external_ref}': {detail}"
        )


class IdempotencyConflictError(BusinessError):
    """Raised when a financial request with an existing idempotency key attempts a duplicate operation."""

    def __init__(self, idempotency_key: str) -> None:
        self.idempotency_key = idempotency_key
        super().__init__(f"Operation with idempotency key '{idempotency_key}' already processed.")


class UnauthorizedFinancialActionError(BusinessError):
    """Raised when a high-risk financial action lacks proper governance approval or violates separation of duties."""

    pass


class GTMError(DomainError):
    """Base exception for Product, Customer & GTM operations errors."""

    pass


class CustomerDataIsolationError(GTMError):
    """Raised when an attempt is made to access another customer's data or workspace across tenant boundaries."""

    def __init__(self, requestor_customer_id: str, target_customer_id: str) -> None:
        self.requestor_customer_id = requestor_customer_id
        self.target_customer_id = target_customer_id
        super().__init__(
            f"Customer isolation violation: Customer '{requestor_customer_id}' context attempted access to '{target_customer_id}' data."
        )


class UnauthorizedCommercialCommitmentError(GTMError):
    """Raised when an unapproved commercial proposal, pricing change, or legal term is attempted without governance."""

    pass


class PricingPolicyViolationError(GTMError):
    """Raised when a discount or price modification breaches corporate policy thresholds without approval."""

    def __init__(self, discount_pct: float, max_allowed_pct: float) -> None:
        self.discount_pct = discount_pct
        self.max_allowed_pct = max_allowed_pct
        super().__init__(
            f"Pricing discount policy violation: requested {discount_pct}%, but maximum automatic limit is {max_allowed_pct}%."
        )


class DuplicateCustomerError(GTMError):
    """Raised when creating a duplicate customer record."""

    def __init__(self, customer_identifier: str) -> None:
        self.customer_identifier = customer_identifier
        super().__init__(f"Customer record for identifier '{customer_identifier}' already exists.")


# --- Phase 25 Multi-Company & Simulation Exceptions ---

class MultiCompanyError(DomainError):
    """Base exception for Multi-Company & Tenancy operations."""

    pass


class TenantIsolationViolationError(MultiCompanyError):
    """Raised when cross-company resource access is attempted without authorization."""

    def __init__(self, requestor_company_id: str, target_company_id: str, resource_type: str = "resource") -> None:
        self.requestor_company_id = requestor_company_id
        self.target_company_id = target_company_id
        self.resource_type = resource_type
        super().__init__(
            f"Tenant isolation violation: Company '{requestor_company_id}' context attempted unauthorized access to {resource_type} belonging to Company '{target_company_id}'."
        )


class CrossCompanyAccessDeniedError(MultiCompanyError):
    """Raised when cross-company relationship or data sharing request is denied or unapproved."""

    def __init__(self, source_company_id: str, target_company_id: str, reason: str = "No approved relationship or active data-share request") -> None:
        self.source_company_id = source_company_id
        self.target_company_id = target_company_id
        self.reason = reason
        super().__init__(
            f"Cross-company access denied between '{source_company_id}' and '{target_company_id}': {reason}."
        )


class CompanyQuotaExceededError(MultiCompanyError):
    """Raised when a company breaches its allocated resource quotas."""

    def __init__(self, company_id: str, quota_name: str, limit: float, requested: float) -> None:
        self.company_id = company_id
        self.quota_name = quota_name
        self.limit = limit
        self.requested = requested
        super().__init__(
            f"Company '{company_id}' quota '{quota_name}' exceeded: limit is {limit}, requested {requested}."
        )


class SimulationError(MultiCompanyError):
    """Base exception for Company Simulation errors."""

    pass


class SimulationProductionMutationError(SimulationError):
    """Raised when a simulation operation attempts to mutate production state or trigger external side effects."""

    def __init__(self, simulation_id: str, attempted_action: str) -> None:
        self.simulation_id = simulation_id
        self.attempted_action = attempted_action
        super().__init__(
            f"Simulation safety violation in simulation '{simulation_id}': Attempted production-mutating action '{attempted_action}'."
        )


class InvalidLifecycleTransitionError(MultiCompanyError):
    """Raised when an invalid company lifecycle transition is attempted."""

    def __init__(self, company_id: str, current_lifecycle: str, target_lifecycle: str) -> None:
        self.company_id = company_id
        self.current_lifecycle = current_lifecycle
        self.target_lifecycle = target_lifecycle
        super().__init__(
            f"Invalid company lifecycle transition for '{company_id}': Cannot transition from '{current_lifecycle}' to '{target_lifecycle}'."
        )


# Phase 26 Company Intelligence & Decision Support Exceptions
class CompanyIntelligenceError(DomainError):
    """Base exception for Company Intelligence & Decision Support domain."""
    pass


class InvalidIntelligenceRunStateError(CompanyIntelligenceError):
    """Raised when an invalid status transition is attempted on an IntelligenceRun."""

    def __init__(self, run_id: str, current_status: str, target_status: str) -> None:
        self.run_id = run_id
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid intelligence run transition for '{run_id}': Cannot transition from '{current_status}' to '{target_status}'."
        )


class DecisionInsightExpiredError(CompanyIntelligenceError):
    """Raised when an action is attempted on an expired decision insight."""

    def __init__(self, insight_id: str, reason: str = "Decision insight has expired.") -> None:
        self.insight_id = insight_id
        self.reason = reason
        super().__init__(f"Decision insight '{insight_id}' is expired: {reason}")


class UnauthorizedDecisionExecutionError(CompanyIntelligenceError):
    """Raised when attempting to execute a recommendation that has not passed human governance approval."""

    def __init__(self, insight_id: str, reason: str = "Human governance approval strictly required prior to execution.") -> None:
        self.insight_id = insight_id
        self.reason = reason
        super().__init__(f"Unauthorized decision execution for insight '{insight_id}': {reason}")


# Phase 27 Continuous Organizational Learning & Governed Adaptation Exceptions
class LearningError(DomainError):
    """Base exception for Continuous Organizational Learning domain."""
    pass


class InvalidLearningCycleStateError(LearningError):
    """Raised when an invalid status transition is attempted on a LearningCycle."""

    def __init__(self, cycle_id: str, current_status: str, target_status: str) -> None:
        self.cycle_id = cycle_id
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid learning cycle status transition for '{cycle_id}': Cannot transition from '{current_status}' to '{target_status}'."
        )


class InvalidAdaptationStateError(LearningError):
    """Raised when an invalid status transition is attempted on an AdaptationProposal."""

    def __init__(self, proposal_id: str, current_status: str, target_status: str) -> None:
        self.proposal_id = proposal_id
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid adaptation proposal status transition for '{proposal_id}': Cannot transition from '{current_status}' to '{target_status}'."
        )


class UnauthorizedAdaptationExecutionError(LearningError):
    """Raised when an adaptation is dispatched or executed without valid human governance approval."""

    def __init__(self, proposal_id: str, reason: str = "Human governance approval strictly required prior to adaptation execution.") -> None:
        self.proposal_id = proposal_id
        self.reason = reason
        super().__init__(f"Unauthorized adaptation execution for proposal '{proposal_id}': {reason}")


class CrossCompanyLearningAccessDeniedError(LearningError):
    """Raised when cross-company learning or adaptation data access is attempted without authorization."""

    def __init__(self, requesting_company_id: str, target_company_id: str) -> None:
        self.requesting_company_id = requesting_company_id
        self.target_company_id = target_company_id
        super().__init__(
            f"Cross-company learning access denied: Company '{requesting_company_id}' cannot access learning data of Company '{target_company_id}'."
        )


class UntrustedLearningInjectionError(LearningError):
    """Raised when an untrusted or unverified learning candidate attempts to override system policies."""

    def __init__(self, candidate_id: str, reason: str = "Untrusted learning candidate cannot override system policy.") -> None:
        self.candidate_id = candidate_id
        self.reason = reason
        super().__init__(f"Untrusted learning injection blocked for candidate '{candidate_id}': {reason}")


class AdaptationRollbackError(LearningError):
    """Raised when an adaptation rollback operation fails or an irreversible adaptation is attempted without authorization."""

    def __init__(self, proposal_id: str, reason: str) -> None:
        self.proposal_id = proposal_id
        self.reason = reason
        super().__init__(f"Adaptation rollback error for proposal '{proposal_id}': {reason}")







