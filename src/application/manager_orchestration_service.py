"""
ManagerOrchestrationService Application Layer.
Coordinates high-level organizational objectives, clarification, planning, decomposition,
capability-based selection, work assignment, blocker resolution, escalation, and execution
delegation.
"""

from src.application.context import ContextItem, ContextSource
from src.application.employee_selector import EmployeeSelector
from src.application.event_dispatcher import EventDispatcher
from src.application.execution_engine import AgentExecutionEngine
from src.application.plan_validator import PlanValidator
from src.domain.assignment import Assignment, AssignmentStatus
from src.domain.decision import DecisionType, ManagerDecision
from src.domain.events import (
    BlockerDetectedEvent,
    ManagerDecisionCreatedEvent,
    ObjectiveClarificationRequestedEvent,
    ObjectiveClarifiedEvent,
    ObjectiveCompletedEvent,
    ObjectiveCreatedEvent,
    PlanApprovedEvent,
    PlanCreatedEvent,
    WorkItemAssignedEvent,
    WorkItemEscalatedEvent,
    WorkItemReassignedEvent,
)
from src.domain.exceptions import (
    AssignmentError,
    EscalationError,
    ObjectiveNotFoundError,
    ObjectiveValidationError,
    PlanValidationError,
)
from src.domain.objective import Objective, ObjectiveStatus
from src.domain.plan import Plan, PlanStatus
from src.domain.repository import (
    AgentRepositoryInterface,
    AssignmentRepositoryInterface,
    DecisionRepositoryInterface,
    EmployeeRepositoryInterface,
    ObjectiveRepositoryInterface,
    PlanRepositoryInterface,
    WorkItemRepositoryInterface,
)
from src.domain.run import AgentRun
from src.domain.work_item import WorkItem, WorkItemStatus


class ManagerOrchestrationService:
    def __init__(
        self,
        objective_repo: ObjectiveRepositoryInterface,
        plan_repo: PlanRepositoryInterface,
        work_item_repo: WorkItemRepositoryInterface,
        assignment_repo: AssignmentRepositoryInterface,
        decision_repo: DecisionRepositoryInterface,
        employee_repo: EmployeeRepositoryInterface,
        agent_repo: AgentRepositoryInterface,
        execution_engine: AgentExecutionEngine,
        plan_validator: PlanValidator | None = None,
        employee_selector: EmployeeSelector | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.objective_repo = objective_repo
        self.plan_repo = plan_repo
        self.work_item_repo = work_item_repo
        self.assignment_repo = assignment_repo
        self.decision_repo = decision_repo
        self.employee_repo = employee_repo
        self.agent_repo = agent_repo
        self.execution_engine = execution_engine
        self.plan_validator = plan_validator or PlanValidator()
        self.employee_selector = employee_selector or EmployeeSelector()
        self.event_dispatcher = event_dispatcher

    async def create_objective(
        self,
        objective_id: str,
        title: str,
        description: str,
        requester: str,
        priority: str = "medium",
        constraints: list[str] | None = None,
        manager_id: str | None = None,
    ) -> Objective:
        """Create and persist a new organizational objective."""
        existing = await self.objective_repo.get_by_id(objective_id)
        if existing is not None:
            raise ObjectiveValidationError(f"Objective with ID '{objective_id}' already exists.")

        if manager_id:
            mgr = await self.employee_repo.get_by_id(manager_id)
            if mgr is None:
                raise ObjectiveValidationError(f"Referenced Manager '{manager_id}' does not exist.")
            if not mgr.is_executable():
                raise ObjectiveValidationError(
                    f"Manager '{manager_id}' is in status '{mgr.status.value}' "
                    "and cannot orchestrate."
                )
            if not mgr.is_manager():
                raise ObjectiveValidationError(
                    f"Employee '{manager_id}' does not possess managerial authority."
                )

        obj = Objective(
            id=objective_id,
            title=title,
            description=description,
            requester=requester,
            priority=priority,
            constraints=constraints or [],
            status=ObjectiveStatus.RECEIVED,
            manager_id=manager_id,
        )

        saved = await self.objective_repo.save(obj)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                ObjectiveCreatedEvent(
                    objective_id=saved.id,
                    title=saved.title,
                    requester=saved.requester,
                    manager_id=saved.manager_id,
                )
            )

        return saved

    async def get_objective(self, objective_id: str) -> Objective:
        """Find an objective by ID or raise ObjectiveNotFoundError."""
        obj = await self.objective_repo.get_by_id(objective_id)
        if obj is None:
            raise ObjectiveNotFoundError(objective_id)
        return obj

    async def request_clarification(self, objective_id: str, questions: list[str]) -> Objective:
        """Request clarification for an ambiguous objective."""
        obj = await self.get_objective(objective_id)
        obj.transition_to(ObjectiveStatus.CLARIFICATION_REQUIRED)
        obj.metadata["clarification_questions"] = questions
        saved = await self.objective_repo.save(obj)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                ObjectiveClarificationRequestedEvent(
                    objective_id=saved.id,
                    questions=questions,
                )
            )

        return saved

    async def provide_clarification(self, objective_id: str, answers: dict[str, str]) -> Objective:
        """Provide clarification answers and transition objective to READY_FOR_PLANNING."""
        obj = await self.get_objective(objective_id)
        if obj.status == ObjectiveStatus.CLARIFICATION_REQUIRED:
            obj.transition_to(ObjectiveStatus.CLARIFYING)

        obj.transition_to(ObjectiveStatus.READY_FOR_PLANNING)
        obj.metadata["clarification_answers"] = answers
        saved = await self.objective_repo.save(obj)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                ObjectiveClarifiedEvent(
                    objective_id=saved.id,
                    answers=answers,
                )
            )

        return saved

    async def submit_and_validate_plan(self, proposed_plan: Plan) -> tuple[Plan, Objective]:
        """Validate and persist an LLM/Manager-proposed plan."""
        obj = await self.get_objective(proposed_plan.objective_id)
        mgr = await self.employee_repo.get_by_id(proposed_plan.manager_id)
        if mgr is None or not mgr.is_executable() or not mgr.is_manager():
            raise PlanValidationError(
                f"Manager '{proposed_plan.manager_id}' is invalid, inactive, or unauthorized."
            )

        # Validate plan structure and business rules
        self.plan_validator.validate_proposed_plan(proposed_plan)

        proposed_plan.status = PlanStatus.PROPOSED
        saved_plan = await self.plan_repo.save(proposed_plan)

        obj.plan_id = saved_plan.id
        if obj.can_transition_to(ObjectiveStatus.PLANNING):
            obj.transition_to(ObjectiveStatus.PLANNING)
        obj.transition_to(ObjectiveStatus.PLANNED)
        saved_obj = await self.objective_repo.save(obj)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                PlanCreatedEvent(
                    plan_id=saved_plan.id,
                    objective_id=saved_obj.id,
                    manager_id=saved_plan.manager_id,
                    work_item_count=len(saved_plan.work_items),
                )
            )

        return saved_plan, saved_obj

    async def approve_plan(self, plan_id: str, manager_id: str) -> Plan:
        """Approve a proposed plan and move objective into EXECUTING state."""
        plan = await self.plan_repo.get_by_id(plan_id)
        if plan is None:
            raise PlanValidationError(f"Plan '{plan_id}' not found.")

        mgr = await self.employee_repo.get_by_id(manager_id)
        if mgr is None or not mgr.is_executable() or not mgr.is_manager():
            raise PlanValidationError(f"Manager '{manager_id}' is unauthorized to approve plan.")

        plan.status = PlanStatus.APPROVED
        saved_plan = await self.plan_repo.save(plan)

        obj = await self.get_objective(plan.objective_id)
        obj.transition_to(ObjectiveStatus.EXECUTING)
        await self.objective_repo.save(obj)

        # Record Manager Decision
        decision = ManagerDecision(
            id=f"dec_{saved_plan.id}",
            manager_id=manager_id,
            objective_id=obj.id,
            decision_type=DecisionType.APPROVE_PLAN,
            reasoning_summary="Plan validated and approved for execution.",
            selected_action="Approve plan and authorize work item assignments.",
        )
        await self.decision_repo.save(decision)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                PlanApprovedEvent(
                    plan_id=saved_plan.id,
                    objective_id=obj.id,
                    approved_by=manager_id,
                )
            )
            await self.event_dispatcher.publish(
                ManagerDecisionCreatedEvent(
                    decision_id=decision.id,
                    manager_id=manager_id,
                    objective_id=obj.id,
                    decision_type=decision.decision_type.value,
                )
            )

        return saved_plan

    async def assign_work_item(
        self,
        work_item_id: str,
        employee_id: str,
        assigned_by_manager_id: str,
        reason: str = "",
    ) -> Assignment:
        """Assign a planned work item to an eligible active employee."""
        wi = await self.work_item_repo.get_by_id(work_item_id)
        if wi is None:
            raise AssignmentError(f"WorkItem '{work_item_id}' not found.")

        mgr = await self.employee_repo.get_by_id(assigned_by_manager_id)
        if mgr is None or not mgr.is_executable() or not mgr.is_manager():
            raise AssignmentError(
                f"Assigned-by manager '{assigned_by_manager_id}' is invalid or unauthorized."
            )

        emp = await self.employee_repo.get_by_id(employee_id)
        if emp is None:
            raise AssignmentError(f"Target employee '{employee_id}' not found.")
        if not emp.is_executable():
            raise AssignmentError(
                f"Target employee '{employee_id}' is in status '{emp.status.value}' "
                "and cannot be assigned work."
            )

        # Validate capability matching
        eligible = self.employee_selector.find_eligible_employees(
            employees=[emp],
            required_capabilities=wi.required_capabilities,
            require_all=True,
        )
        if not eligible:
            raise AssignmentError(
                f"Employee '{employee_id}' lacks required capabilities "
                f"{wi.required_capabilities} for work item '{wi.title}'."
            )

        # Save Assignment
        assignment = Assignment(
            id=f"asgn_{work_item_id}_{employee_id}",
            work_item_id=work_item_id,
            employee_id=employee_id,
            assigned_by=assigned_by_manager_id,
            reason=reason,
            status=AssignmentStatus.ACTIVE,
        )
        saved_asgn = await self.assignment_repo.save(assignment)

        # Update WorkItem
        wi.assigned_employee_id = employee_id
        wi.status = WorkItemStatus.ASSIGNED
        await self.work_item_repo.save(wi)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                WorkItemAssignedEvent(
                    work_item_id=wi.id,
                    employee_id=employee_id,
                    assigned_by=assigned_by_manager_id,
                )
            )

        return saved_asgn

    async def reassign_work_item(
        self,
        work_item_id: str,
        new_employee_id: str,
        assigned_by_manager_id: str,
        reason: str,
    ) -> Assignment:
        """Reassign a work item to a new eligible employee, archiving historical assignment."""
        wi = await self.work_item_repo.get_by_id(work_item_id)
        if wi is None:
            raise AssignmentError(f"WorkItem '{work_item_id}' not found.")

        prev_emp_id = wi.assigned_employee_id

        # Deactivate previous active assignments
        if prev_emp_id:
            existing_asgns = await self.assignment_repo.list_by_work_item_id(work_item_id)
            for a in existing_asgns:
                if a.status == AssignmentStatus.ACTIVE:
                    a.status = AssignmentStatus.REASSIGNED
                    await self.assignment_repo.save(a)

        new_asgn = await self.assign_work_item(
            work_item_id=work_item_id,
            employee_id=new_employee_id,
            assigned_by_manager_id=assigned_by_manager_id,
            reason=reason,
        )

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                WorkItemReassignedEvent(
                    work_item_id=work_item_id,
                    previous_employee_id=prev_emp_id,
                    new_employee_id=new_employee_id,
                    reason=reason,
                )
            )

        return new_asgn

    async def handle_blocker(
        self, work_item_id: str, objective_id: str, employee_id: str, reason: str
    ) -> WorkItem:
        """Record work item blocker and update objective state."""
        wi = await self.work_item_repo.get_by_id(work_item_id)
        if wi is None:
            raise AssignmentError(f"WorkItem '{work_item_id}' not found.")

        wi.status = WorkItemStatus.BLOCKED
        wi.blocker_reason = reason
        saved_wi = await self.work_item_repo.save(wi)

        obj = await self.get_objective(objective_id)
        if obj.can_transition_to(ObjectiveStatus.BLOCKED):
            obj.transition_to(ObjectiveStatus.BLOCKED)
            await self.objective_repo.save(obj)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                BlockerDetectedEvent(
                    work_item_id=work_item_id,
                    objective_id=objective_id,
                    employee_id=employee_id,
                    reason=reason,
                )
            )

        return saved_wi

    async def escalate_work_item(
        self, work_item_id: str, objective_id: str, manager_id: str, reason: str
    ) -> ManagerDecision:
        """Escalate a blocked work item to the manager's manager in the hierarchy."""
        mgr = await self.employee_repo.get_by_id(manager_id)
        if mgr is None or not mgr.manager_id:
            raise EscalationError(f"Manager '{manager_id}' has no higher manager to escalate to.")

        higher_mgr_id = mgr.manager_id

        decision = ManagerDecision(
            id=f"esc_{work_item_id}",
            manager_id=manager_id,
            objective_id=objective_id,
            decision_type=DecisionType.ESCALATE,
            reasoning_summary=f"Escalated work item '{work_item_id}': {reason}",
            selected_action=f"Escalate to higher manager '{higher_mgr_id}'",
        )
        saved_dec = await self.decision_repo.save(decision)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                WorkItemEscalatedEvent(
                    work_item_id=work_item_id,
                    objective_id=objective_id,
                    escalated_by=manager_id,
                    escalated_to=higher_mgr_id,
                    reason=reason,
                )
            )

        return saved_dec

    async def complete_objective(self, objective_id: str, manager_id: str) -> Objective:
        """Mark an objective as COMPLETED after manager review."""
        obj = await self.get_objective(objective_id)
        mgr = await self.employee_repo.get_by_id(manager_id)
        if mgr is None or not mgr.is_executable() or not mgr.is_manager():
            raise ObjectiveValidationError(
                f"Manager '{manager_id}' is unauthorized to complete objective."
            )

        obj.transition_to(ObjectiveStatus.COMPLETED)
        saved_obj = await self.objective_repo.save(obj)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                ObjectiveCompletedEvent(
                    objective_id=saved_obj.id,
                    manager_id=manager_id,
                )
            )

        return saved_obj

    async def execute_manager_objective(
        self,
        objective_id: str,
        manager_id: str,
    ) -> AgentRun:
        """
        Execute manager orchestration objective by constructing manager organizational context
        and delegating directly to Phase 1 AgentExecutionEngine.
        """
        obj = await self.get_objective(objective_id)
        mgr = await self.employee_repo.get_by_id(manager_id)
        if mgr is None:
            raise ObjectiveValidationError(f"Manager '{manager_id}' not found.")
        if not mgr.is_executable():
            raise ObjectiveValidationError(
                f"Manager '{manager_id}' is in status '{mgr.status.value}' "
                "and cannot orchestrate."
            )
        if not mgr.is_manager():
            raise ObjectiveValidationError(
                f"Employee '{manager_id}' does not possess managerial authority."
            )

        # Build Manager Execution Context
        context_text = (
            f"ORGANIZATIONAL MANAGER PROFILE:\n"
            f"- Manager Employee ID: {mgr.id}\n"
            f"- Manager Name: {mgr.name}\n"
            f"- Title: {mgr.title}\n"
            f"- Role: {mgr.role}\n\n"
            f"TARGET ORGANIZATIONAL OBJECTIVE:\n"
            f"- Objective ID: {obj.id}\n"
            f"- Title: {obj.title}\n"
            f"- Description: {obj.description}\n"
            f"- Requester: {obj.requester}\n"
            f"- Priority: {obj.priority}\n"
            f"- Constraints: {', '.join(obj.constraints) if obj.constraints else 'None'}\n\n"
            f"YOUR MANAGER RESPONSIBILITIES:\n"
            f"1. Analyze objective for ambiguity.\n"
            f"2. Decompose objective into structured work items.\n"
            f"3. Specify required capabilities for work items.\n"
            f"4. Propose an executable plan.\n"
        )

        context_item = ContextItem(
            source=ContextSource.SYSTEM,
            content=context_text,
            priority=2,
        )

        return await self.execution_engine.execute_run(
            agent_id=mgr.agent_id,
            objective=f"Orchestrate Objective '{obj.id}': {obj.title}",
            extra_context_items=[context_item],
        )
