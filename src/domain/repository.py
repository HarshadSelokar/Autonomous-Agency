"""
Domain repository interfaces.
Follows the repository pattern to keep domain decoupled from persistence details.
"""

from abc import ABC, abstractmethod

from src.domain.agent import Agent
from src.domain.checkpoint import AgentCheckpoint
from src.domain.department import Department
from src.domain.employee import Employee
from src.domain.run import AgentRun
from src.domain.step import ExecutionStep


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
