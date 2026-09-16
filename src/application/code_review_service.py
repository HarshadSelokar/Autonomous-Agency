"""
CodeReviewService Application Layer for Phase 9 AI Software Company.
Manages code change proposals, reviewer assignments, review evaluations, self-approval guards,
and integration with Phase 4 Task Engine rework loops.
"""

from src.application.event_dispatcher import EventDispatcher
from src.domain.events import (
    CodeChangeCreatedEvent,
    CodeReviewApprovedEvent,
    CodeReviewChangesRequestedEvent,
    CodeReviewRequestedEvent,
)
from src.domain.exceptions import UnauthorizedApprovalError
from src.domain.software_company import (
    CodeChange,
    CodeChangeStatus,
    CodeReview,
    CodeReviewStatus,
)
from src.domain.task import TaskStatus
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemyCodeReviewRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository


class CodeReviewService:
    def __init__(
        self,
        change_repo: SQLAlchemyCodeChangeRepository,
        review_repo: SQLAlchemyCodeReviewRepository,
        task_repo: SQLAlchemyTaskRepository,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.change_repo = change_repo
        self.review_repo = review_repo
        self.task_repo = task_repo
        self.event_dispatcher = event_dispatcher

    async def submit_code_change(
        self,
        project_id: str,
        task_id: str,
        author_employee_id: str,
        files_changed: list[str],
        diff_summary: str,
        agent_run_id: str = "",
        workspace_id: str = "",
        branch_name: str = "main",
    ) -> CodeChange:
        """Submit a new CodeChange for a task."""
        change = CodeChange(
            project_id=project_id,
            task_id=task_id,
            author_employee_id=author_employee_id,
            agent_run_id=agent_run_id,
            workspace_id=workspace_id,
            branch_name=branch_name,
            files_changed=files_changed,
            diff_summary=diff_summary,
            status=CodeChangeStatus.PROPOSED,
        )
        saved = await self.change_repo.save(change)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                CodeChangeCreatedEvent(
                    change_id=saved.change_id,
                    project_id=project_id,
                    task_id=task_id,
                    author_employee_id=author_employee_id,
                    branch_name=branch_name,
                )
            )

        return saved

    async def request_code_review(
        self,
        change_id: str,
        reviewer_employee_id: str,
    ) -> CodeReview:
        """Request a code review for a proposed change."""
        change = await self.change_repo.get_by_id(change_id)
        if change is None:
            raise ValueError(f"CodeChange '{change_id}' not found.")

        # Self-approval guard check
        if change.author_employee_id == reviewer_employee_id:
            raise UnauthorizedApprovalError(
                f"Employee '{reviewer_employee_id}' cannot review or approve their own code change."
            )

        review = CodeReview(
            change_id=change_id,
            reviewer_employee_id=reviewer_employee_id,
            status=CodeReviewStatus.PENDING,
        )
        saved_review = await self.review_repo.save(review)

        change.status = CodeChangeStatus.READY_FOR_REVIEW
        await self.change_repo.save(change)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                CodeReviewRequestedEvent(
                    review_id=saved_review.review_id,
                    change_id=change_id,
                    reviewer_employee_id=reviewer_employee_id,
                )
            )

        return saved_review

    async def submit_review_findings(
        self,
        review_id: str,
        status: CodeReviewStatus,
        findings: list[str],
        recommendations: str = "",
        evidence_id: str | None = None,
    ) -> tuple[CodeReview, CodeChange]:
        """
        Submit code review results. If APPROVED, change status becomes APPROVED.
        If CHANGES_REQUESTED, change status becomes CHANGES_REQUESTED and triggers task rework.
        """
        review = await self.review_repo.get_by_id(review_id)
        if review is None:
            raise ValueError(f"CodeReview '{review_id}' not found.")

        change = await self.change_repo.get_by_id(review.change_id)
        if change is None:
            raise ValueError(f"CodeChange '{review.change_id}' not found.")

        # Self-approval guard
        if change.author_employee_id == review.reviewer_employee_id:
            raise UnauthorizedApprovalError(
                f"Employee '{review.reviewer_employee_id}' cannot approve their own code change."
            )

        review.status = status
        review.findings = findings
        review.recommendations = recommendations
        review.evidence_id = evidence_id
        saved_review = await self.review_repo.save(review)

        if status == CodeReviewStatus.APPROVED:
            change.status = CodeChangeStatus.APPROVED
            await self.change_repo.save(change)

            if self.event_dispatcher:
                await self.event_dispatcher.publish(
                    CodeReviewApprovedEvent(
                        review_id=saved_review.review_id,
                        change_id=change.change_id,
                        reviewer_employee_id=review.reviewer_employee_id,
                    )
                )

        elif status == CodeReviewStatus.CHANGES_REQUESTED:
            change.status = CodeChangeStatus.CHANGES_REQUESTED
            await self.change_repo.save(change)

            # Trigger Task REWORK in Phase 4 Task Engine
            task = await self.task_repo.get_by_id(change.task_id)
            if task:
                task.retry_count += 1
                if task.can_transition_to(TaskStatus.REWORK):
                    task.transition_to(TaskStatus.REWORK)
                else:
                    task.status = TaskStatus.REWORK
                await self.task_repo.save(task)


            if self.event_dispatcher:
                await self.event_dispatcher.publish(
                    CodeReviewChangesRequestedEvent(
                        review_id=saved_review.review_id,
                        change_id=change.change_id,
                        reviewer_employee_id=review.reviewer_employee_id,
                        findings=findings,
                    )
                )

        return saved_review, change
