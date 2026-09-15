"""
SoftwareProjectService Application Layer for Phase 9 AI Software Company.
Coordinates software project creation, requirements analysis, engineering planning,
capability-based task assignment, and backend-authoritative project status aggregation.
"""

from typing import Any
import uuid
from src.application.employee_selector import EmployeeSelector

from src.application.event_dispatcher import EventDispatcher
from src.domain.events import (
    EngineeringPlanCreatedEvent,
    SoftwareProjectCreatedEvent,
    SoftwareRequirementCreatedEvent,
)
from src.domain.exceptions import ObjectiveValidationError
from src.domain.repository import (
    AssignmentRepositoryInterface,
    EmployeeRepositoryInterface,
    ObjectiveRepositoryInterface,
)
from src.domain.software_company import (
    CodeChangeStatus,
    DefectStatus,
    DeliveryStatus,
    EngineeringPlan,
    RequirementPriority,
    RequirementStatus,
    SoftwareProject,
    SoftwareProjectStatus,
    SoftwareRequirement,
    TestRunStatus,
)
from src.domain.task import Task, TaskStatus

from src.domain.task_dependency import DependencyType, TaskDependency

from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemyCodeReviewRepository,
    SQLAlchemyEngineeringPlanRepository,
    SQLAlchemySoftwareDefectRepository,
    SQLAlchemySoftwareDeliveryRepository,
    SQLAlchemySoftwareProjectRepository,
    SQLAlchemySoftwareRequirementRepository,
    SQLAlchemyTestRunRepository,
)

from src.infrastructure.repositories.task_dependency_repository import SQLAlchemyTaskDependencyRepository
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


class SoftwareProjectService:
    def __init__(
        self,
        project_repo: SQLAlchemySoftwareProjectRepository,
        req_repo: SQLAlchemySoftwareRequirementRepository,
        task_repo: SQLAlchemyTaskRepository,
        dep_repo: SQLAlchemyTaskDependencyRepository,
        employee_repo: EmployeeRepositoryInterface,
        assignment_repo: AssignmentRepositoryInterface,
        objective_repo: ObjectiveRepositoryInterface,
        plan_repo: SQLAlchemyEngineeringPlanRepository | None = None,
        change_repo: SQLAlchemyCodeChangeRepository | None = None,

        review_repo: SQLAlchemyCodeReviewRepository | None = None,
        test_repo: SQLAlchemyTestRunRepository | None = None,
        defect_repo: SQLAlchemySoftwareDefectRepository | None = None,
        delivery_repo: SQLAlchemySoftwareDeliveryRepository | None = None,
        employee_selector: EmployeeSelector | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.project_repo = project_repo
        self.req_repo = req_repo
        self.task_repo = task_repo
        self.dep_repo = dep_repo
        self.employee_repo = employee_repo
        self.assignment_repo = assignment_repo
        self.objective_repo = objective_repo
        self.plan_repo = plan_repo
        self.change_repo = change_repo
        self.review_repo = review_repo
        self.test_repo = test_repo
        self.defect_repo = defect_repo
        self.delivery_repo = delivery_repo
        self.employee_selector = employee_selector or EmployeeSelector()
        self.event_dispatcher = event_dispatcher


    async def create_software_project(
        self,
        objective_id: str,
        name: str,
        description: str = "",
        repository_path: str = "",
        workspace_id: str = "",
    ) -> SoftwareProject:
        """Create a new SoftwareProject linked to an existing organizational Objective."""
        obj = await self.objective_repo.get_by_id(objective_id)
        if obj is None:
            raise ObjectiveValidationError(f"Objective '{objective_id}' not found.")

        existing = await self.project_repo.get_by_objective_id(objective_id)
        if existing is not None:
            return existing

        project = SoftwareProject(
            name=name,
            description=description or obj.description,
            objective_id=objective_id,
            repository_path=repository_path,
            workspace_id=workspace_id,
            status=SoftwareProjectStatus.CREATED,
        )
        saved = await self.project_repo.save(project)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                SoftwareProjectCreatedEvent(
                    project_id=saved.project_id,
                    objective_id=saved.objective_id,
                    name=saved.name,
                    repository_path=saved.repository_path,
                )
            )

        return saved

    async def add_requirements(
        self,
        project_id: str,
        requirements_data: list[dict[str, Any]],
    ) -> list[SoftwareRequirement]:
        """Add structured requirements to a SoftwareProject."""
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise ValueError(f"SoftwareProject '{project_id}' not found.")

        added_reqs: list[SoftwareRequirement] = []
        for item in requirements_data:
            p_str = item.get("priority", "MEDIUM").upper()
            priority_enum = RequirementPriority[p_str] if p_str in RequirementPriority.__members__ else RequirementPriority.MEDIUM

            req = SoftwareRequirement(
                project_id=project_id,
                title=item["title"],
                description=item.get("description", ""),
                acceptance_criteria=item.get("acceptance_criteria", []),
                priority=priority_enum,
                status=RequirementStatus.ANALYZED,
            )
            saved_req = await self.req_repo.save(req)
            added_reqs.append(saved_req)

            if self.event_dispatcher:
                await self.event_dispatcher.publish(
                    SoftwareRequirementCreatedEvent(
                        requirement_id=saved_req.requirement_id,
                        project_id=project_id,
                        title=saved_req.title,
                        priority=saved_req.priority.value,
                    )
                )

        project.status = SoftwareProjectStatus.REQUIREMENTS_ANALYSIS
        await self.project_repo.save(project)
        return added_reqs

    async def create_engineering_plan(
        self,
        project_id: str,
        manager_employee_id: str,
        architecture_overview: str,
        tech_stack: list[str],
    ) -> EngineeringPlan:
        """
        Decomposes software requirements into Phase 4 Task Graph (Architecture, Implementation, QA, Review).
        """
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise ValueError(f"SoftwareProject '{project_id}' not found.")

        mgr = await self.employee_repo.get_by_id(manager_employee_id)
        if mgr is None or not mgr.is_manager():
            raise ValueError(f"Employee '{manager_employee_id}' is not an authorized Engineering Manager.")

        reqs = await self.req_repo.list_by_project(project_id)
        if not reqs:
            raise ValueError(f"SoftwareProject '{project_id}' has no requirements to plan.")

        created_tasks: list[Task] = []
        deps_to_create: list[tuple[str, str]] = []

        # 1. Architecture Task
        arch_task = Task(
            id=f"task_arch_{uuid.uuid4().hex[:8]}",
            plan_id=project_id,
            objective_id=project.objective_id,
            title=f"Architecture Specification - {project.name}",
            description=f"Define system design and API schemas. Architecture overview: {architecture_overview}",
            required_capabilities=["SOFTWARE_ARCHITECTURE"],
            priority="high",
            status=TaskStatus.READY,
        )
        arch_task = await self.task_repo.save(arch_task)
        created_tasks.append(arch_task)

        prev_task_id = arch_task.id

        # 2. Requirement Implementation Tasks
        for idx, req in enumerate(reqs, start=1):
            dev_task = Task(
                id=f"task_dev_{uuid.uuid4().hex[:8]}",
                plan_id=project_id,
                objective_id=project.objective_id,
                title=f"Feature Dev: {req.title}",
                description=f"{req.description}\nAcceptance Criteria: {', '.join(req.acceptance_criteria)}",
                required_capabilities=["BACKEND_DEVELOPMENT"],
                priority="high" if req.priority == RequirementPriority.HIGH else "medium",
                status=TaskStatus.BLOCKED,
            )
            dev_task = await self.task_repo.save(dev_task)
            created_tasks.append(dev_task)

            deps_to_create.append((prev_task_id, dev_task.id))
            prev_task_id = dev_task.id

            # Requirement status -> APPROVED
            req.status = RequirementStatus.APPROVED
            await self.req_repo.save(req)

        # 3. QA Testing Task
        qa_task = Task(
            id=f"task_qa_{uuid.uuid4().hex[:8]}",
            plan_id=project_id,
            objective_id=project.objective_id,
            title=f"QA Test Suite Execution - {project.name}",
            description="Run integration/unit test suite, record TestRun evidence, and verify acceptance criteria.",
            required_capabilities=["QA_ENGINEERING"],
            priority="high",
            status=TaskStatus.BLOCKED,
        )
        qa_task = await self.task_repo.save(qa_task)
        created_tasks.append(qa_task)
        deps_to_create.append((prev_task_id, qa_task.id))

        # 4. Code Review Task
        review_task = Task(
            id=f"task_rev_{uuid.uuid4().hex[:8]}",
            plan_id=project_id,
            objective_id=project.objective_id,
            title=f"Final Code Review - {project.name}",
            description="Perform code review on proposed code changes and verify overall quality.",
            required_capabilities=["CODE_REVIEW"],
            priority="high",
            status=TaskStatus.BLOCKED,
        )
        review_task = await self.task_repo.save(review_task)
        created_tasks.append(review_task)
        deps_to_create.append((qa_task.id, review_task.id))


        # Persist task dependencies in Task Engine
        for pred_id, succ_id in deps_to_create:
            dep = TaskDependency(
                id=f"dep_{uuid.uuid4().hex[:8]}",
                predecessor_task_id=pred_id,
                successor_task_id=succ_id,
                dependency_type=DependencyType.BLOCKING,
            )
            await self.dep_repo.save(dep)

        plan = EngineeringPlan(
            project_id=project_id,
            manager_employee_id=manager_employee_id,
            architecture_overview=architecture_overview,
            tech_stack=tech_stack,
            task_ids=[t.id for t in created_tasks],
        )
        if self.plan_repo:
            await self.plan_repo.save(plan)

        project.engineering_plan = plan
        project.status = SoftwareProjectStatus.PLANNING
        await self.project_repo.save(project)


        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                EngineeringPlanCreatedEvent(
                    plan_id=plan.plan_id,
                    project_id=project_id,
                    manager_employee_id=manager_employee_id,
                    task_count=len(created_tasks),
                )
            )

        return plan

    async def assign_engineering_tasks(self, project_id: str) -> dict[str, str]:
        """
        Uses EmployeeSelector to capability-match active employees for ready/planned tasks.
        Returns a mapping of task_id -> assigned_employee_id.
        """
        project = await self.project_repo.get_by_id(project_id)
        if project is None or not project.engineering_plan:
            raise ValueError(f"Project '{project_id}' does not have an engineering plan.")

        active_employees = await self.employee_repo.list_all()
        active_employees = [e for e in active_employees if e.is_executable()]

        assignments: dict[str, str] = {}
        for task_id in project.engineering_plan.task_ids:
            task = await self.task_repo.get_by_id(task_id)
            if not task or task.assigned_employee_id:
                continue

            eligible = self.employee_selector.find_eligible_employees(
                employees=active_employees,
                required_capabilities=task.required_capabilities,
                require_all=False,
            )

            if eligible:
                selected_emp = eligible[0]
                task.assigned_employee_id = selected_emp.id
                await self.task_repo.save(task)
                assignments[task.id] = selected_emp.id

        project.status = SoftwareProjectStatus.IN_DEVELOPMENT
        await self.project_repo.save(project)
        return assignments

    async def get_project_status(self, project_id: str) -> dict[str, Any]:
        """Derives authoritative project status metrics directly from backend state."""
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise ValueError(f"SoftwareProject '{project_id}' not found.")

        reqs = await self.req_repo.list_by_project(project_id)

        plan = project.engineering_plan
        if not plan and self.plan_repo:
            plan = await self.plan_repo.get_by_project(project_id)

        task_statuses = {}
        if plan:
            for t_id in plan.task_ids:
                t = await self.task_repo.get_by_id(t_id)
                if t:
                    task_statuses[t_id] = t.status.value


        changes = await self.change_repo.list_by_project(project_id) if self.change_repo else []
        test_runs = await self.test_repo.list_by_project(project_id) if self.test_repo else []
        defects = await self.defect_repo.list_by_project(project_id) if self.defect_repo else []

        open_defects = [d for d in defects if d.status not in (DefectStatus.CLOSED, DefectStatus.VERIFIED)]
        passing_tests = [tr for tr in test_runs if tr.status == TestRunStatus.PASSED]

        return {
            "project_id": project_id,
            "name": project.name,
            "status": project.status.value,
            "requirements_count": len(reqs),
            "tasks_count": len(task_statuses),
            "task_statuses": task_statuses,
            "code_changes_count": len(changes),
            "approved_code_changes": len([c for c in changes if c.status == CodeChangeStatus.APPROVED]),
            "test_runs_count": len(test_runs),
            "passing_test_runs": len(passing_tests),
            "open_defects_count": len(open_defects),
        }
