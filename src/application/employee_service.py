"""
Employee Application Service.
Orchestrates employee management and integrates Employee execution with Phase 1 Agent Runtime.
"""

from typing import Any

from src.application.context import ContextItem, ContextSource
from src.application.event_dispatcher import EventDispatcher
from src.application.execution_engine import AgentExecutionEngine
from src.domain.employee import Employee, EmployeeStatus
from src.domain.events import (
    EmployeeCreatedEvent,
    EmployeeDepartmentAssignedEvent,
    EmployeeManagerAssignedEvent,
    EmployeeStatusChangedEvent,
    EmployeeWorkExecutedEvent,
)
from src.domain.exceptions import EmployeeNotFoundError, EmployeeValidationError
from src.domain.repository import (
    AgentRepositoryInterface,
    DepartmentRepositoryInterface,
    EmployeeRepositoryInterface,
)
from src.domain.run import AgentRun, RunStatus


class EmployeeService:
    def __init__(
        self,
        employee_repo: EmployeeRepositoryInterface,
        agent_repo: AgentRepositoryInterface,
        execution_engine: AgentExecutionEngine,
        department_repo: DepartmentRepositoryInterface | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.employee_repo = employee_repo
        self.agent_repo = agent_repo
        self.execution_engine = execution_engine
        self.department_repo = department_repo
        self.event_dispatcher = event_dispatcher

    async def create_employee(self, employee: Employee) -> Employee:
        """Create and register a new Employee entity."""
        # 1. Check for duplicate ID or employee_code
        existing_id = await self.employee_repo.get_by_id(employee.id)
        if existing_id is not None:
            raise EmployeeValidationError(f"Employee with ID '{employee.id}' already exists.")

        existing_code = await self.employee_repo.get_by_code(employee.employee_code)
        if existing_code is not None:
            raise EmployeeValidationError(
                f"Employee code '{employee.employee_code}' is already assigned."
            )

        # 2. Verify associated Agent exists in AgentRepository
        agent = await self.agent_repo.get_by_id(employee.agent_id)
        if agent is None:
            raise EmployeeValidationError(
                f"Referenced Agent '{employee.agent_id}' does not exist in AgentRepository."
            )

        # 3. Verify Manager if assigned and check for hierarchy cycles
        if employee.manager_id:
            await self.validate_manager_hierarchy(employee.id, employee.manager_id)

        # 4. Verify Department if assigned
        if employee.department_id and self.department_repo is not None:
            department = await self.department_repo.get_by_id(employee.department_id)
            if department is None:
                raise EmployeeValidationError(
                    f"Referenced Department '{employee.department_id}' does not exist."
                )

        saved = await self.employee_repo.save(employee)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                EmployeeCreatedEvent(
                    employee_id=saved.id,
                    employee_code=saved.employee_code,
                    name=saved.name,
                    title=saved.title,
                    role=saved.role,
                    agent_id=saved.agent_id,
                    department_id=saved.department_id,
                    manager_id=saved.manager_id,
                )
            )

        return saved

    async def get_employee(self, employee_id: str) -> Employee:
        """Get an Employee by ID, raising EmployeeNotFoundError if missing."""
        emp = await self.employee_repo.get_by_id(employee_id)
        if emp is None:
            raise EmployeeNotFoundError(employee_id)
        return emp

    async def list_employees(self) -> list[Employee]:
        """List all registered employees."""
        return await self.employee_repo.list_all()

    async def change_status(self, employee_id: str, new_status: EmployeeStatus) -> Employee:
        """Change employee status adhering to lifecycle transition rules."""
        emp = await self.get_employee(employee_id)
        prev_status = emp.status
        emp.transition_to(new_status)
        saved = await self.employee_repo.save(emp)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                EmployeeStatusChangedEvent(
                    employee_id=saved.id,
                    previous_status=prev_status,
                    new_status=saved.status,
                )
            )

        return saved

    async def validate_manager_hierarchy(
        self, employee_id: str, proposed_manager_id: str | None
    ) -> None:
        """
        Validate that proposed_manager_id exists and does not create a
        circular management hierarchy.
        """
        if not proposed_manager_id:
            return

        if proposed_manager_id == employee_id:
            raise EmployeeValidationError(
                f"Employee '{employee_id}' cannot be assigned as their own manager."
            )

        visited = {employee_id}
        current_id: str | None = proposed_manager_id

        while current_id:
            if current_id in visited:
                raise EmployeeValidationError(
                    f"Circular manager hierarchy detected for employee '{employee_id}' "
                    f"via manager '{current_id}'."
                )
            visited.add(current_id)
            mgr = await self.employee_repo.get_by_id(current_id)
            if mgr is None:
                raise EmployeeValidationError(f"Referenced Manager '{current_id}' does not exist.")
            current_id = mgr.manager_id

    async def update_manager(self, employee_id: str, manager_id: str | None) -> Employee:
        """Update manager assignment for an employee with hierarchy cycle validation."""
        emp = await self.get_employee(employee_id)
        if manager_id:
            await self.validate_manager_hierarchy(employee_id, manager_id)

        prev_manager_id = emp.manager_id
        emp.manager_id = manager_id
        saved = await self.employee_repo.save(emp)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                EmployeeManagerAssignedEvent(
                    employee_id=saved.id,
                    previous_manager_id=prev_manager_id,
                    new_manager_id=saved.manager_id,
                )
            )

        return saved

    async def update_department(self, employee_id: str, department_id: str | None) -> Employee:
        """Update department assignment for an employee."""
        emp = await self.get_employee(employee_id)
        if department_id and self.department_repo is not None:
            dept = await self.department_repo.get_by_id(department_id)
            if dept is None:
                raise EmployeeValidationError(f"Department '{department_id}' does not exist.")

        prev_dept_id = emp.department_id
        emp.department_id = department_id
        saved = await self.employee_repo.save(emp)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                EmployeeDepartmentAssignedEvent(
                    employee_id=saved.id,
                    previous_department_id=prev_dept_id,
                    new_department_id=saved.department_id,
                )
            )

        return saved

    async def execute_work(
        self,
        employee_id: str,
        objective: str,
        task_id: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> AgentRun:
        """
        Execute organizational work for an Employee by building organizational context
        and delegating to Phase 1 AgentExecutionEngine.
        """
        # 1. Load Employee
        emp = await self.get_employee(employee_id)

        # 2. Check Execution Authorization (Active status guardrail)
        if not emp.is_executable():
            raise EmployeeValidationError(
                f"Employee '{employee_id}' ({emp.name}) is in status '{emp.status.value}' "
                "and is not authorized to execute work."
            )

        # 3. Build Organizational Execution Context Items
        skills_text = (
            ", ".join(f"{s.name} ({s.proficiency.value})" for s in emp.skills)
            if emp.skills
            else "standard skills"
        )
        caps_text = (
            ", ".join(f"{c.name}" for c in emp.capabilities)
            if emp.capabilities
            else "general capability"
        )
        resp_text = (
            "\n".join(f"  * {r}" for r in emp.responsibilities)
            if emp.responsibilities
            else "  * Standard employee duties"
        )

        org_context_text = (
            f"ORGANIZATIONAL EMPLOYEE PROFILE:\n"
            f"- Employee ID: {emp.id}\n"
            f"- Employee Code: {emp.employee_code}\n"
            f"- Employee Name: {emp.name}\n"
            f"- Title: {emp.title}\n"
            f"- Role: {emp.role}\n"
            f"- Department ID: {emp.department_id or 'Unassigned'}\n"
            f"- Manager ID: {emp.manager_id or 'None'}\n\n"
            f"EMPLOYEE SKILLS & CAPABILITIES:\n"
            f"Skills: {skills_text}\n"
            f"Capabilities: {caps_text}\n"
            f"Assigned Responsibilities:\n{resp_text}"
        )

        org_context_item = ContextItem(
            source=ContextSource.SYSTEM,
            content=org_context_text,
            priority=2,  # Priority right after base system prompt
        )

        # 4. Delegate Execution directly to Phase 1 AgentExecutionEngine
        run = await self.execution_engine.execute_run(
            agent_id=emp.agent_id,
            objective=objective,
            task_id=task_id,
            response_schema=response_schema,
            extra_context_items=[org_context_item],
        )

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                EmployeeWorkExecutedEvent(
                    employee_id=emp.id,
                    agent_id=emp.agent_id,
                    run_id=run.id,
                    objective=objective,
                    success=(run.status == RunStatus.COMPLETED),
                )
            )

        return run
