"""
Domain repository interfaces.
Follows the repository pattern to keep domain decoupled from persistence details.
"""

from abc import ABC, abstractmethod

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

