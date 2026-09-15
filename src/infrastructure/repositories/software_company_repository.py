"""
SQLAlchemy Repositories for Phase 9 AI Software Company persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.software_company import (
    CodeChange,
    CodeChangeStatus,
    CodeReview,
    CodeReviewStatus,
    DefectSeverity,
    DefectStatus,
    DeliveryStatus,
    EngineeringPlan,
    RequirementPriority,
    RequirementStatus,
    SoftwareDefect,
    SoftwareDelivery,
    SoftwareProject,
    SoftwareProjectStatus,
    SoftwareRequirement,
    TestRun,
    TestRunStatus,
)
from src.infrastructure.models.software_company_model import (
    CodeChangeModel,
    CodeReviewModel,
    EngineeringPlanModel,
    SoftwareDefectModel,
    SoftwareDeliveryModel,
    SoftwareProjectModel,
    SoftwareRequirementModel,
    TestRunModel,
    project_domain_to_model,
    project_model_to_domain,
)


class SQLAlchemySoftwareProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, project: SoftwareProject) -> SoftwareProject:
        model = project_domain_to_model(project)
        merged = await self.session.merge(model)
        await self.session.flush()
        return project_model_to_domain(merged)

    async def get_by_id(self, project_id: str) -> SoftwareProject | None:
        stmt = select(SoftwareProjectModel).where(SoftwareProjectModel.id == project_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return project_model_to_domain(model) if model else None

    async def get_by_objective_id(self, objective_id: str) -> SoftwareProject | None:
        stmt = select(SoftwareProjectModel).where(SoftwareProjectModel.objective_id == objective_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return project_model_to_domain(model) if model else None


class SQLAlchemySoftwareRequirementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, req: SoftwareRequirement) -> SoftwareRequirement:
        p_str = req.priority.value if hasattr(req.priority, "value") else str(req.priority)
        s_str = req.status.value if hasattr(req.status, "value") else str(req.status)
        model = SoftwareRequirementModel(
            id=req.requirement_id,
            project_id=req.project_id,
            title=req.title,
            description=req.description,
            acceptance_criteria=req.acceptance_criteria,
            priority=p_str,
            status=s_str,
            clarification_notes=req.clarification_notes,
            created_at=req.created_at,
            updated_at=req.updated_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return req

    async def get_by_id(self, req_id: str) -> SoftwareRequirement | None:
        stmt = select(SoftwareRequirementModel).where(SoftwareRequirementModel.id == req_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return SoftwareRequirement(
            requirement_id=model.id,
            project_id=model.project_id,
            title=model.title,
            description=model.description,
            acceptance_criteria=model.acceptance_criteria or [],
            priority=RequirementPriority(model.priority),
            status=RequirementStatus(model.status),
            clarification_notes=model.clarification_notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_by_project(self, project_id: str) -> list[SoftwareRequirement]:
        stmt = select(SoftwareRequirementModel).where(SoftwareRequirementModel.project_id == project_id)
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [
            SoftwareRequirement(
                requirement_id=m.id,
                project_id=m.project_id,
                title=m.title,
                description=m.description,
                acceptance_criteria=m.acceptance_criteria or [],
                priority=RequirementPriority(m.priority),
                status=RequirementStatus(m.status),
                clarification_notes=m.clarification_notes,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]


class SQLAlchemyCodeChangeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, change: CodeChange) -> CodeChange:
        s_str = change.status.value if hasattr(change.status, "value") else str(change.status)
        model = CodeChangeModel(
            id=change.change_id,
            project_id=change.project_id,
            task_id=change.task_id,
            author_employee_id=change.author_employee_id,
            agent_run_id=change.agent_run_id,
            workspace_id=change.workspace_id,
            branch_name=change.branch_name,
            files_changed=change.files_changed,
            diff_summary=change.diff_summary,
            status=s_str,
            commit_hash=change.commit_hash,
            created_at=change.created_at,
            updated_at=change.updated_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return change

    async def get_by_id(self, change_id: str) -> CodeChange | None:
        stmt = select(CodeChangeModel).where(CodeChangeModel.id == change_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return CodeChange(
            change_id=model.id,
            project_id=model.project_id,
            task_id=model.task_id,
            author_employee_id=model.author_employee_id,
            agent_run_id=model.agent_run_id,
            workspace_id=model.workspace_id,
            branch_name=model.branch_name,
            files_changed=model.files_changed or [],
            diff_summary=model.diff_summary,
            status=CodeChangeStatus(model.status),
            commit_hash=model.commit_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_by_project(self, project_id: str) -> list[CodeChange]:
        stmt = select(CodeChangeModel).where(CodeChangeModel.project_id == project_id)
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [
            CodeChange(
                change_id=m.id,
                project_id=m.project_id,
                task_id=m.task_id,
                author_employee_id=m.author_employee_id,
                agent_run_id=m.agent_run_id,
                workspace_id=m.workspace_id,
                branch_name=m.branch_name,
                files_changed=m.files_changed or [],
                diff_summary=m.diff_summary,
                status=CodeChangeStatus(m.status),
                commit_hash=m.commit_hash,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]


class SQLAlchemyCodeReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, review: CodeReview) -> CodeReview:
        s_str = review.status.value if hasattr(review.status, "value") else str(review.status)
        model = CodeReviewModel(
            id=review.review_id,
            change_id=review.change_id,
            reviewer_employee_id=review.reviewer_employee_id,
            status=s_str,
            findings=review.findings,
            recommendations=review.recommendations,
            evidence_id=review.evidence_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return review

    async def get_by_id(self, review_id: str) -> CodeReview | None:
        stmt = select(CodeReviewModel).where(CodeReviewModel.id == review_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return CodeReview(
            review_id=model.id,
            change_id=model.change_id,
            reviewer_employee_id=model.reviewer_employee_id,
            status=CodeReviewStatus(model.status),
            findings=model.findings or [],
            recommendations=model.recommendations,
            evidence_id=model.evidence_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemyTestRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, test_run: TestRun) -> TestRun:
        s_str = test_run.status.value if hasattr(test_run.status, "value") else str(test_run.status)
        model = TestRunModel(
            id=test_run.test_run_id,
            project_id=test_run.project_id,
            task_id=test_run.task_id,
            worker_employee_id=test_run.worker_employee_id,
            agent_run_id=test_run.agent_run_id,
            workspace_id=test_run.workspace_id,
            command=test_run.command,
            exit_code=test_run.exit_code,
            total_tests=test_run.total_tests,
            passed_count=test_run.passed_count,
            failed_count=test_run.failed_count,
            skipped_count=test_run.skipped_count,
            output_reference=test_run.output_reference,
            evidence_id=test_run.evidence_id,
            status=s_str,
            created_at=test_run.created_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return test_run

    async def get_by_id(self, test_run_id: str) -> TestRun | None:
        stmt = select(TestRunModel).where(TestRunModel.id == test_run_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return TestRun(
            test_run_id=model.id,
            project_id=model.project_id,
            task_id=model.task_id,
            worker_employee_id=model.worker_employee_id,
            agent_run_id=model.agent_run_id,
            workspace_id=model.workspace_id,
            command=model.command,
            exit_code=model.exit_code,
            total_tests=model.total_tests,
            passed_count=model.passed_count,
            failed_count=model.failed_count,
            skipped_count=model.skipped_count,
            output_reference=model.output_reference,
            evidence_id=model.evidence_id,
            status=TestRunStatus(model.status),
            created_at=model.created_at,
        )

    async def list_by_project(self, project_id: str) -> list[TestRun]:
        stmt = select(TestRunModel).where(TestRunModel.project_id == project_id)
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [
            TestRun(
                test_run_id=m.id,
                project_id=m.project_id,
                task_id=m.task_id,
                worker_employee_id=m.worker_employee_id,
                agent_run_id=m.agent_run_id,
                workspace_id=m.workspace_id,
                command=m.command,
                exit_code=m.exit_code,
                total_tests=m.total_tests,
                passed_count=m.passed_count,
                failed_count=m.failed_count,
                skipped_count=m.skipped_count,
                output_reference=m.output_reference,
                evidence_id=m.evidence_id,
                status=TestRunStatus(m.status),
                created_at=m.created_at,
            )
            for m in models
        ]


class SQLAlchemySoftwareDefectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, defect: SoftwareDefect) -> SoftwareDefect:
        sev_str = defect.severity.value if hasattr(defect.severity, "value") else str(defect.severity)
        stat_str = defect.status.value if hasattr(defect.status, "value") else str(defect.status)
        model = SoftwareDefectModel(
            id=defect.defect_id,
            project_id=defect.project_id,
            title=defect.title,
            description=defect.description,
            severity=sev_str,
            status=stat_str,
            reproduction_steps=defect.reproduction_steps,
            originating_task_id=defect.originating_task_id,
            fix_task_id=defect.fix_task_id,
            assigned_employee_id=defect.assigned_employee_id,
            verification_test_run_id=defect.verification_test_run_id,
            created_at=defect.created_at,
            updated_at=defect.updated_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return defect

    async def get_by_id(self, defect_id: str) -> SoftwareDefect | None:
        stmt = select(SoftwareDefectModel).where(SoftwareDefectModel.id == defect_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return SoftwareDefect(
            defect_id=model.id,
            project_id=model.project_id,
            title=model.title,
            description=model.description,
            severity=DefectSeverity(model.severity),
            status=DefectStatus(model.status),
            reproduction_steps=model.reproduction_steps,
            originating_task_id=model.originating_task_id,
            fix_task_id=model.fix_task_id,
            assigned_employee_id=model.assigned_employee_id,
            verification_test_run_id=model.verification_test_run_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def list_by_project(self, project_id: str) -> list[SoftwareDefect]:
        stmt = select(SoftwareDefectModel).where(SoftwareDefectModel.project_id == project_id)
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [
            SoftwareDefect(
                defect_id=m.id,
                project_id=m.project_id,
                title=m.title,
                description=m.description,
                severity=DefectSeverity(m.severity),
                status=DefectStatus(m.status),
                reproduction_steps=m.reproduction_steps,
                originating_task_id=m.originating_task_id,
                fix_task_id=m.fix_task_id,
                assigned_employee_id=m.assigned_employee_id,
                verification_test_run_id=m.verification_test_run_id,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]


class SQLAlchemySoftwareDeliveryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, delivery: SoftwareDelivery) -> SoftwareDelivery:
        stat_str = delivery.status.value if hasattr(delivery.status, "value") else str(delivery.status)
        model = SoftwareDeliveryModel(
            id=delivery.delivery_id,
            project_id=delivery.project_id,
            version=delivery.version,
            commit_hash=delivery.commit_hash,
            requested_by_employee_id=delivery.requested_by_employee_id,
            approved_by_employee_id=delivery.approved_by_employee_id,
            status=stat_str,
            evidence_summary=delivery.evidence_summary,
            created_at=delivery.created_at,
            updated_at=delivery.updated_at,
        )
        merged = await self.session.merge(model)
        await self.session.flush()
        return delivery

    async def get_by_id(self, delivery_id: str) -> SoftwareDelivery | None:
        stmt = select(SoftwareDeliveryModel).where(SoftwareDeliveryModel.id == delivery_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if not model:
            return None
        return SoftwareDelivery(
            delivery_id=model.id,
            project_id=model.project_id,
            version=model.version,
            commit_hash=model.commit_hash,
            requested_by_employee_id=model.requested_by_employee_id,
            approved_by_employee_id=model.approved_by_employee_id,
            status=DeliveryStatus(model.status),
            evidence_summary=model.evidence_summary or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
