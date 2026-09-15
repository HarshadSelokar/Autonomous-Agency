"""
SoftwareDeliveryService Application Layer for Phase 9 AI Software Company.
Controls software delivery release requests, approval verification, evidence evaluation,
and self-approval governance boundaries.
"""

from src.application.event_dispatcher import EventDispatcher
from src.domain.events import SoftwareDeliveryApprovedEvent, SoftwareDeliveredEvent
from src.domain.exceptions import UnauthorizedApprovalError
from src.domain.software_company import (
    CodeChangeStatus,
    DefectStatus,
    DeliveryStatus,
    SoftwareDelivery,
    TestRunStatus,
)
from src.infrastructure.repositories.software_company_repository import (
    SQLAlchemyCodeChangeRepository,
    SQLAlchemySoftwareDefectRepository,
    SQLAlchemySoftwareDeliveryRepository,
    SQLAlchemySoftwareProjectRepository,
    SQLAlchemySoftwareRequirementRepository,
    SQLAlchemyTestRunRepository,
)


class SoftwareDeliveryService:
    def __init__(
        self,
        delivery_repo: SQLAlchemySoftwareDeliveryRepository,
        project_repo: SQLAlchemySoftwareProjectRepository,
        req_repo: SQLAlchemySoftwareRequirementRepository,
        change_repo: SQLAlchemyCodeChangeRepository,
        test_repo: SQLAlchemyTestRunRepository,
        defect_repo: SQLAlchemySoftwareDefectRepository,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.delivery_repo = delivery_repo
        self.project_repo = project_repo
        self.req_repo = req_repo
        self.change_repo = change_repo
        self.test_repo = test_repo
        self.defect_repo = defect_repo
        self.event_dispatcher = event_dispatcher

    async def request_delivery(
        self,
        project_id: str,
        requested_by_employee_id: str,
        version: str = "1.0.0",
        commit_hash: str = "main",
    ) -> SoftwareDelivery:
        """Create a SoftwareDelivery request pending manager approval."""
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise ValueError(f"SoftwareProject '{project_id}' not found.")

        delivery = SoftwareDelivery(
            project_id=project_id,
            version=version,
            commit_hash=commit_hash,
            requested_by_employee_id=requested_by_employee_id,
            status=DeliveryStatus.PENDING_APPROVAL,
        )
        return await self.delivery_repo.save(delivery)

    async def approve_delivery(
        self,
        delivery_id: str,
        approved_by_employee_id: str,
    ) -> SoftwareDelivery:
        """
        Approve release delivery after validating:
        1. Requester != Approver (Self-approval guard).
        2. All code changes APPROVED.
        3. At least one passing TestRun.
        4. No OPEN or ASSIGNED defects remaining.
        """
        delivery = await self.delivery_repo.get_by_id(delivery_id)
        if delivery is None:
            raise ValueError(f"SoftwareDelivery '{delivery_id}' not found.")

        # 1. Self-approval Guard
        if delivery.requested_by_employee_id == approved_by_employee_id:
            raise UnauthorizedApprovalError(
                f"Employee '{approved_by_employee_id}' cannot approve their own software delivery request."
            )

        # 2. Check Code Changes
        changes = await self.change_repo.list_by_project(delivery.project_id)
        unapproved_changes = [c for c in changes if c.status != CodeChangeStatus.APPROVED]
        if unapproved_changes:
            raise ValueError(
                f"Cannot approve delivery: {len(unapproved_changes)} code changes are not approved."
            )

        # 3. Check Test Runs
        test_runs = await self.test_repo.list_by_project(delivery.project_id)
        passing_tests = [tr for tr in test_runs if tr.status == TestRunStatus.PASSED]
        if not passing_tests:
            raise ValueError("Cannot approve delivery: No passing TestRun evidence recorded for project.")

        # 4. Check Open Defects
        defects = await self.defect_repo.list_by_project(delivery.project_id)
        open_defects = [d for d in defects if d.status not in (DefectStatus.CLOSED, DefectStatus.VERIFIED)]
        if open_defects:
            raise ValueError(f"Cannot approve delivery: {len(open_defects)} unresolved defects remaining.")

        delivery.approved_by_employee_id = approved_by_employee_id
        delivery.status = DeliveryStatus.APPROVED
        delivery.status = DeliveryStatus.DELIVERED
        delivery.evidence_summary = {
            "approved_by": approved_by_employee_id,
            "passing_tests_count": len(passing_tests),
            "approved_code_changes_count": len(changes),
            "closed_defects_count": len(defects) - len(open_defects),
        }

        saved_delivery = await self.delivery_repo.save(delivery)

        if self.event_dispatcher:
            await self.event_dispatcher.publish(
                SoftwareDeliveryApprovedEvent(
                    delivery_id=saved_delivery.delivery_id,
                    project_id=delivery.project_id,
                    approved_by_employee_id=approved_by_employee_id,
                )
            )
            await self.event_dispatcher.publish(
                SoftwareDeliveredEvent(
                    delivery_id=saved_delivery.delivery_id,
                    project_id=delivery.project_id,
                    version=saved_delivery.version,
                    commit_hash=saved_delivery.commit_hash,
                )
            )

        return saved_delivery
