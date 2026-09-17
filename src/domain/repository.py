"""
Domain repository interfaces.
Follows the repository pattern to keep domain decoupled from persistence details.
"""

from abc import ABC, abstractmethod
from typing import Any


from src.domain.agent import Agent
from src.domain.assignment import Assignment
from src.domain.checkpoint import AgentCheckpoint
from src.domain.decision import ManagerDecision
from src.domain.department import Department
from src.domain.employee import Employee
from src.domain.objective import Objective
from src.domain.plan import Plan
from src.domain.run import AgentRun
from src.domain.step import ExecutionStep
from src.domain.work_item import WorkItem


class AgentRepositoryInterface(ABC):
    """Abstract interface for Agent persistence operations."""

    @abstractmethod
    async def save(self, agent: Agent) -> Agent:
        """Save or update an Agent entity."""
        pass

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Agent | None:
        """Find an Agent entity by its ID."""
        pass

    @abstractmethod
    async def list_all(self) -> list[Agent]:
        """List all persisted Agent entities."""
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """Delete an Agent entity by ID. Returns True if deleted."""
        pass


class AgentRunRepositoryInterface(ABC):
    """Abstract interface for AgentRun persistence operations."""

    @abstractmethod
    async def save(self, run: AgentRun) -> AgentRun:
        """Save or update an AgentRun entity."""
        pass

    @abstractmethod
    async def get_by_id(self, run_id: str) -> AgentRun | None:
        """Find an AgentRun entity by ID."""
        pass

    @abstractmethod
    async def list_by_agent_id(self, agent_id: str) -> list[AgentRun]:
        """List all AgentRuns for a specific agent."""
        pass


class ExecutionStepRepositoryInterface(ABC):
    """Abstract interface for ExecutionStep persistence operations."""

    @abstractmethod
    async def save(self, step: ExecutionStep) -> ExecutionStep:
        """Save or update an ExecutionStep entity."""
        pass

    @abstractmethod
    async def list_by_run_id(self, run_id: str) -> list[ExecutionStep]:
        """List all ExecutionSteps for a specific run in order of step_number."""
        pass


class CheckpointRepositoryInterface(ABC):
    """Abstract interface for AgentCheckpoint persistence operations."""

    @abstractmethod
    async def save(self, checkpoint: AgentCheckpoint) -> AgentCheckpoint:
        """Save an AgentCheckpoint entity."""
        pass

    @abstractmethod
    async def get_latest_by_run_id(self, run_id: str) -> AgentCheckpoint | None:
        """Find the latest checkpoint for a specific run."""
        pass

    @abstractmethod
    async def list_by_run_id(self, run_id: str) -> list[AgentCheckpoint]:
        """List all checkpoints for a specific run ordered by timestamp."""
        pass


class EmployeeRepositoryInterface(ABC):
    """Abstract interface for Employee persistence operations."""

    @abstractmethod
    async def save(self, employee: Employee) -> Employee:
        """Save or update an Employee entity."""
        pass

    @abstractmethod
    async def get_by_id(self, employee_id: str) -> Employee | None:
        """Find an Employee by ID."""
        pass

    @abstractmethod
    async def get_by_code(self, employee_code: str) -> Employee | None:
        """Find an Employee by employee_code."""
        pass

    @abstractmethod
    async def list_all(self) -> list[Employee]:
        """List all Employee entities."""
        pass

    @abstractmethod
    async def list_by_department_id(self, department_id: str) -> list[Employee]:
        """List all Employees assigned to a specific department."""
        pass

    @abstractmethod
    async def delete(self, employee_id: str) -> bool:
        """Delete or archive an Employee by ID."""
        pass


class DepartmentRepositoryInterface(ABC):
    """Abstract interface for Department persistence operations."""

    @abstractmethod
    async def save(self, department: Department) -> Department:
        """Save or update a Department entity."""
        pass

    @abstractmethod
    async def get_by_id(self, department_id: str) -> Department | None:
        """Find a Department by ID."""
        pass

    @abstractmethod
    async def list_all(self) -> list[Department]:
        """List all Department entities."""
        pass


class ObjectiveRepositoryInterface(ABC):
    """Abstract interface for Objective persistence operations."""

    @abstractmethod
    async def save(self, objective: "Objective") -> "Objective":
        """Save or update an Objective entity."""
        pass

    @abstractmethod
    async def get_by_id(self, objective_id: str) -> "Objective | None":
        """Find an Objective by ID."""
        pass

    @abstractmethod
    async def list_all(self) -> "list[Objective]":
        """List all Objective entities."""
        pass

    @abstractmethod
    async def list_by_manager_id(self, manager_id: str) -> "list[Objective]":
        """List Objectives assigned to a specific manager."""
        pass


class PlanRepositoryInterface(ABC):
    """Abstract interface for Plan persistence operations."""

    @abstractmethod
    async def save(self, plan: "Plan") -> "Plan":
        """Save or update a Plan entity."""
        pass

    @abstractmethod
    async def get_by_id(self, plan_id: str) -> "Plan | None":
        """Find a Plan by ID."""
        pass

    @abstractmethod
    async def get_by_objective_id(self, objective_id: str) -> "Plan | None":
        """Find the Plan associated with an objective."""
        pass


class WorkItemRepositoryInterface(ABC):
    """Abstract interface for WorkItem persistence operations."""

    @abstractmethod
    async def save(self, work_item: "WorkItem") -> "WorkItem":
        """Save or update a WorkItem entity."""
        pass

    @abstractmethod
    async def get_by_id(self, work_item_id: str) -> "WorkItem | None":
        """Find a WorkItem by ID."""
        pass

    @abstractmethod
    async def list_by_plan_id(self, plan_id: str) -> "list[WorkItem]":
        """List all WorkItems in a specific Plan."""
        pass


class AssignmentRepositoryInterface(ABC):
    """Abstract interface for Assignment persistence operations."""

    @abstractmethod
    async def save(self, assignment: "Assignment") -> "Assignment":
        """Save or update an Assignment entity."""
        pass

    @abstractmethod
    async def get_by_id(self, assignment_id: str) -> "Assignment | None":
        """Find an Assignment by ID."""
        pass

    @abstractmethod
    async def list_by_work_item_id(self, work_item_id: str) -> "list[Assignment]":
        """List all historical Assignments for a work item."""
        pass


class DecisionRepositoryInterface(ABC):
    """Abstract interface for ManagerDecision persistence operations."""

    @abstractmethod
    async def save(self, decision: "ManagerDecision") -> "ManagerDecision":
        """Save or update a ManagerDecision entity."""
        pass

    @abstractmethod
    async def get_by_id(self, decision_id: str) -> "ManagerDecision | None":
        """Find a ManagerDecision by ID."""
        pass

    @abstractmethod
    async def list_by_objective_id(self, objective_id: str) -> "list[ManagerDecision]":
        """List all decisions associated with an objective."""
        pass


class MeetingRepositoryInterface(ABC):
    """Abstract interface for Meeting persistence operations."""

    @abstractmethod
    async def save(self, meeting: "Meeting") -> "Meeting":
        """Save or update a Meeting entity."""
        pass

    @abstractmethod
    async def get_by_id(self, meeting_id: str) -> "Meeting | None":
        """Find a Meeting by ID."""
        pass

    @abstractmethod
    async def list_all(self) -> "list[Meeting]":
        """List all Meetings."""
        pass

    @abstractmethod
    async def list_by_participant(self, employee_id: str) -> "list[Meeting]":
        """List all Meetings where the employee is a participant."""
        pass


class MemoryRepositoryInterface(ABC):
    """Abstract interface for MemoryEntry persistence operations."""

    @abstractmethod
    async def save(self, memory: "MemoryEntry") -> "MemoryEntry":
        """Save or update a MemoryEntry entity."""
        pass

    @abstractmethod
    async def get_by_id(self, memory_id: str) -> "MemoryEntry | None":
        """Find a MemoryEntry by ID."""
        pass

    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> "list[MemoryEntry]":
        """List all active memories for a given owner ID."""
        pass

    @abstractmethod
    async def list_all(self) -> "list[MemoryEntry]":
        """List all memories."""
        pass


class SwarmRepositoryInterface(ABC):
    """Abstract interface for Swarm persistence operations (Phase 22)."""

    @abstractmethod
    async def save(self, swarm: Any) -> Any:
        """Save or update a Swarm aggregate root."""
        pass

    @abstractmethod
    async def get_by_id(self, swarm_id: str) -> Any | None:
        """Find a Swarm by ID."""
        pass

    @abstractmethod
    async def list_all(self) -> list[Any]:
        """List all Swarms."""
        pass

    @abstractmethod
    async def list_by_parent_task(self, parent_task_id: str) -> list[Any]:
        """List Swarms for a specific parent task."""
        pass


class BusinessRepositoryInterface(ABC):
    """Abstract interface for Business Operations & Financial persistence (Phase 23)."""

    @abstractmethod
    async def save_account(self, account: Any) -> Any:
        pass

    @abstractmethod
    async def get_account_by_id(self, account_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_accounts(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_transaction(self, transaction: Any) -> Any:
        pass

    @abstractmethod
    async def get_transaction_by_id(self, transaction_id: str) -> Any | None:
        pass

    @abstractmethod
    async def get_transaction_by_idempotency_key(self, idempotency_key: str) -> Any | None:
        pass

    @abstractmethod
    async def list_transactions(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_invoice(self, invoice: Any) -> Any:
        pass

    @abstractmethod
    async def get_invoice_by_id(self, invoice_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_invoices(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_revenue(self, revenue: Any) -> Any:
        pass

    @abstractmethod
    async def list_revenues(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_expense(self, expense: Any) -> Any:
        pass

    @abstractmethod
    async def list_expenses(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_payment(self, payment: Any) -> Any:
        pass

    @abstractmethod
    async def get_payment_by_id(self, payment_id: str) -> Any | None:
        pass

    @abstractmethod
    async def get_payment_by_idempotency_key(self, idempotency_key: str) -> Any | None:
        pass

    @abstractmethod
    async def list_payments(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_procurement(self, request: Any) -> Any:
        pass

    @abstractmethod
    async def get_procurement_by_id(self, request_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_procurements(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_budget(self, budget: Any) -> Any:
        pass

    @abstractmethod
    async def get_budget_by_id(self, budget_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_budgets(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_reconciliation(self, reconciliation: Any) -> Any:
        pass

    @abstractmethod
    async def get_reconciliation_by_id(self, reconciliation_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_reconciliations(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_metric(self, metric: Any) -> Any:
        pass

    @abstractmethod
    async def list_metrics(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_cash_flow(self, snapshot: Any) -> Any:
        pass

    @abstractmethod
    async def get_latest_cash_flow(self) -> Any | None:
        pass


class GTMRepositoryInterface(ABC):
    """Abstract interface for Product, Customer & GTM persistence operations (Phase 24)."""

    @abstractmethod
    async def save_product(self, product: Any) -> Any:
        pass

    @abstractmethod
    async def get_product_by_id(self, product_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_products(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_product_requirement(self, requirement: Any) -> Any:
        pass

    @abstractmethod
    async def list_product_requirements(self, product_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_product_feedback(self, feedback: Any) -> Any:
        pass

    @abstractmethod
    async def list_product_feedback(self, product_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_customer(self, customer: Any) -> Any:
        pass

    @abstractmethod
    async def get_customer_by_id(self, customer_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_customers(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_customer_interaction(self, interaction: Any) -> Any:
        pass

    @abstractmethod
    async def list_customer_interactions(self, customer_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_lead(self, lead: Any) -> Any:
        pass

    @abstractmethod
    async def get_lead_by_id(self, lead_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_leads(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_opportunity(self, opportunity: Any) -> Any:
        pass

    @abstractmethod
    async def get_opportunity_by_id(self, opportunity_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_opportunities(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_proposal(self, proposal: Any) -> Any:
        pass

    @abstractmethod
    async def get_proposal_by_id(self, proposal_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_proposals(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_support_case(self, support_case: Any) -> Any:
        pass

    @abstractmethod
    async def get_support_case_by_id(self, case_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_support_cases(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_marketing_campaign(self, campaign: Any) -> Any:
        pass

    @abstractmethod
    async def get_marketing_campaign_by_id(self, campaign_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_marketing_campaigns(self) -> list[Any]:
        pass


class MultiCompanyRepositoryInterface(ABC):
    """Abstract Repository Interface for Multi-Company & Simulation Operations."""

    @abstractmethod
    async def save_company(self, company: Any) -> Any:
        pass

    @abstractmethod
    async def get_company_by_id(self, company_id: str) -> Any | None:
        pass

    @abstractmethod
    async def get_company_by_slug(self, slug: str) -> Any | None:
        pass

    @abstractmethod
    async def list_companies(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_company_profile(self, profile: Any) -> Any:
        pass

    @abstractmethod
    async def get_company_profile(self, company_id: str) -> Any | None:
        pass

    @abstractmethod
    async def save_membership(self, membership: Any) -> Any:
        pass

    @abstractmethod
    async def list_memberships_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def list_memberships_for_user(self, user_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_template(self, template: Any) -> Any:
        pass

    @abstractmethod
    async def get_template_by_id(self, template_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_templates(self) -> list[Any]:
        pass

    @abstractmethod
    async def save_relationship(self, relationship: Any) -> Any:
        pass

    @abstractmethod
    async def list_relationships_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_data_share_request(self, request: Any) -> Any:
        pass

    @abstractmethod
    async def get_data_share_request_by_id(self, request_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_data_share_requests_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_resource_quota(self, quota: Any) -> Any:
        pass

    @abstractmethod
    async def get_resource_quota_by_company_id(self, company_id: str) -> Any | None:
        pass

    @abstractmethod
    async def save_resource_usage(self, usage: Any) -> Any:
        pass

    @abstractmethod
    async def get_resource_usage_by_company_id(self, company_id: str) -> Any | None:
        pass

    @abstractmethod
    async def save_simulation(self, simulation: Any) -> Any:
        pass

    @abstractmethod
    async def get_simulation_by_id(self, simulation_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_simulations_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_simulation_snapshot(self, snapshot: Any) -> Any:
        pass

    @abstractmethod
    async def get_simulation_snapshot_by_id(self, snapshot_id: str) -> Any | None:
        pass

    @abstractmethod
    async def save_simulation_scenario(self, scenario: Any) -> Any:
        pass

    @abstractmethod
    async def get_simulation_scenario_by_id(self, scenario_id: str) -> Any | None:
        pass

    @abstractmethod
    async def save_simulation_result(self, result: Any) -> Any:
        pass

    @abstractmethod
    async def get_simulation_result_by_simulation_id(self, simulation_id: str) -> Any | None:
        pass

    @abstractmethod
    async def save_simulation_financial_record(self, record: Any) -> Any:
        pass

    @abstractmethod
    async def list_simulation_financial_records(self, simulation_id: str) -> list[Any]:
        pass


class CompanyIntelligenceRepositoryInterface(ABC):
    """Abstract Repository Interface for Company Intelligence & Decision Support Operations."""

    @abstractmethod
    async def save_intelligence_run(self, run: Any) -> Any:
        pass

    @abstractmethod
    async def get_intelligence_run_by_id(self, run_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_intelligence_runs_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_intelligence_finding(self, finding: Any) -> Any:
        pass

    @abstractmethod
    async def list_findings_for_run(self, run_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_decision_question(self, question: Any) -> Any:
        pass

    @abstractmethod
    async def get_decision_question_by_id(self, question_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_decision_questions_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_decision_option(self, option: Any) -> Any:
        pass

    @abstractmethod
    async def list_options_for_question(self, question_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_decision_evaluation(self, evaluation: Any) -> Any:
        pass

    @abstractmethod
    async def get_evaluation_for_option(self, option_id: str) -> Any | None:
        pass

    @abstractmethod
    async def save_decision_insight(self, insight: Any) -> Any:
        pass

    @abstractmethod
    async def get_decision_insight_by_id(self, insight_id: str) -> Any | None:
        pass

    @abstractmethod
    async def get_decision_insight_by_question_id(self, question_id: str) -> Any | None:
        pass

    @abstractmethod
    async def list_decision_insights_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_company_health_assessment(self, assessment: Any) -> Any:
        pass

    @abstractmethod
    async def get_latest_health_assessment_for_company(self, company_id: str) -> Any | None:
        pass

    @abstractmethod
    async def save_company_bottleneck(self, bottleneck: Any) -> Any:
        pass

    @abstractmethod
    async def list_active_bottlenecks_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_risk_assessment(self, risk: Any) -> Any:
        pass

    @abstractmethod
    async def list_risks_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_opportunity_assessment(self, opportunity: Any) -> Any:
        pass

    @abstractmethod
    async def list_opportunities_for_company(self, company_id: str) -> list[Any]:
        pass

    @abstractmethod
    async def save_decision_outcome_evaluation(self, evaluation: Any) -> Any:
        pass

    @abstractmethod
    async def get_outcome_evaluation_by_insight_id(self, insight_id: str) -> Any | None:
        pass







