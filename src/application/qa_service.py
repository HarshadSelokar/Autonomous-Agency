"""
QAService Application Layer for Phase 9 AI Software Company.
Manages test run execution evidence, failure evaluation, defect reporting,
and defect-to-task resolution workflows.
"""

import uuid

from src.application.event_dispatcher import EventDispatcher
from src.domain.events import (
    SoftwareDefectCreatedEvent,
    SoftwareDefectFixedEvent,
    TestRunFailedEvent,
    TestRunStartedEvent,
    TestRunSucceededEvent,
)
from src.domain.software_company import (
    DefectSeverity,
    DefectStatus,
    SoftwareDefect,
    TestRun,
    TestRunStatus,
)
from src.domain.task import Task, TaskStatus
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemySoftwareDefectRepository,
    SQLAlchemyTestRunRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


class QAService:
    def __init__(
        self,
        test_repo: SQLAlchemyTestRunRepository,
        defect_repo: SQLAlchemySoftwareDefectRepository,
        task_repo: SQLAlchemyTaskRepository,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.test_repo = test_repo
        self.defect_repo = defect_repo
        self.task_repo = task_repo
        self.event_dispatcher = event_dispatcher

    async def record_test_run(
        self,
        project_id: str,
        task_id: str,
        worker_employee_id: str,
        command: str,
        exit_code: int,
        total_tests: int,
        passed_count: int,
        failed_count: int,
        output_reference: str = "",
        skipped_count: int = 0,
        agent_run_id: str = "",
        workspace_id: str = "",
        evidence_id: str | None = None,
    ) -> TestRun:
        """
        Record a TestRun based on actual tool execution results.
        Status is PASSED if exit_code == 0 and failed_count == 0, else FAILED.
        """
        status = TestRunStatus.PASSED if (exit_code == 0 and failed_count == 0) else TestRunStatus.FAILED

        test_run = TestRun(
            project_id=project_id,
            task_id=task_id,
            worker_employee_id=worker_employee_id,
            agent_run_id=agent_run_id,
            workspace_id=workspace_id,
            command=command,
            exit_code=exit_code,
            total_tests=total_tests,
            passed_count=passed_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            output_reference=output_reference,
            evidence_id=evidence_id,
            status=status,
        )
        saved = await self.test_repo.save(test_run)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                TestRunStartedEvent(
                    test_run_id=saved.test_run_id,
                    task_id=task_id,
                    workspace_id=workspace_id,
                    command=command,
                )
            )
            if status == TestRunStatus.PASSED:
                await self.event_dispatcher.publish(
                    TestRunSucceededEvent(
                        test_run_id=saved.test_run_id,
                        task_id=task_id,
                        passed_count=passed_count,
                    )
                )
            else:
                await self.event_dispatcher.publish(
                    TestRunFailedEvent(
                        test_run_id=saved.test_run_id,
                        task_id=task_id,
                        failed_count=failed_count,
                        error_summary=output_reference,
                    )
                )

        return saved

    async def report_defect(
        self,
        project_id: str,
        title: str,
        description: str = "",
        severity: DefectSeverity = DefectSeverity.MEDIUM,
        reproduction_steps: str = "",
        originating_task_id: str | None = None,
        assigned_employee_id: str | None = None,
    ) -> tuple[SoftwareDefect, Task]:
        """
        Report a SoftwareDefect and generate a corresponding bugfix Task in the Task Engine.
        """
        # Create bugfix task in Task Engine
        fix_task = Task(
            id=f"task_fix_{uuid.uuid4().hex[:8]}",
            plan_id=project_id,
            title=f"Bugfix: {title}",
            description=f"Defect description: {description}\nReproduction Steps: {reproduction_steps}",
            required_capabilities=["BACKEND_DEVELOPMENT"],
            priority="critical" if severity in (DefectSeverity.HIGH, DefectSeverity.CRITICAL) else "high",
            status=TaskStatus.READY,
            assigned_employee_id=assigned_employee_id,
        )
        saved_task = await self.task_repo.save(fix_task)


        defect = SoftwareDefect(
            project_id=project_id,
            title=title,
            description=description,
            severity=severity,
            status=DefectStatus.OPEN,
            reproduction_steps=reproduction_steps,
            originating_task_id=originating_task_id,
            fix_task_id=saved_task.id,
            assigned_employee_id=assigned_employee_id,
        )
        saved_defect = await self.defect_repo.save(defect)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                SoftwareDefectCreatedEvent(
                    defect_id=saved_defect.defect_id,
                    project_id=project_id,
                    title=title,
                    severity=severity.value,
                    originating_task_id=originating_task_id,
                )
            )

        return saved_defect, saved_task

    async def verify_defect_fix(
        self,
        defect_id: str,
        verification_test_run_id: str,
    ) -> SoftwareDefect:
        """Verify defect fix using a successful TestRun evidence."""
        defect = await self.defect_repo.get_by_id(defect_id)
        if defect is None:
            raise ValueError(f"SoftwareDefect '{defect_id}' not found.")

        test_run = await self.test_repo.get_by_id(verification_test_run_id)
        if test_run is None:
            raise ValueError(f"TestRun '{verification_test_run_id}' not found.")

        if test_run.status != TestRunStatus.PASSED:
            raise ValueError(
                f"Verification TestRun '{verification_test_run_id}' failed with status '{test_run.status.value}'."
            )

        defect.verification_test_run_id = verification_test_run_id
        defect.status = DefectStatus.VERIFIED
        defect.status = DefectStatus.CLOSED
        saved_defect = await self.defect_repo.save(defect)

        if self.event_dispatcher and defect.fix_task_id:
            await self.event_dispatcher.publish(
                SoftwareDefectFixedEvent(
                    defect_id=saved_defect.defect_id,
                    fix_task_id=defect.fix_task_id,
                )
            )

        return saved_defect
