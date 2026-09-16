"""
FastAPI Routes for Phase 9 AI Software Company REST API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.software import (
    AddRequirementsRequest,
    ApproveDeliveryRequest,
    CodeChangeResponse,
    CodeReviewResponse,
    CreateEngineeringPlanRequest,
    CreateSoftwareProjectRequest,
    EngineeringPlanResponse,
    RecordTestRunRequest,
    ReportDefectRequest,
    RequestCodeReviewRequest,
    RequestDeliveryRequest,
    SoftwareDefectResponse,
    SoftwareDeliveryResponse,
    SoftwareProjectResponse,
    SoftwareRequirementResponse,
    SubmitCodeChangeRequest,
    SubmitReviewFindingsRequest,
    TestRunResponse,
)
from src.application.code_review_service import CodeReviewService
from src.application.qa_service import QAService
from src.application.software_delivery_service import SoftwareDeliveryService
from src.application.software_project_service import SoftwareProjectService
from src.domain.exceptions import UnauthorizedApprovalError
from src.domain.software_company import (
    CodeReviewStatus,
    DefectSeverity,
    SoftwareProject,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.assignment_repository import SQLAlchemyAssignmentRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.objective_repository import SQLAlchemyObjectiveRepository
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
from src.infrastructure.repositories.task_dependency_repository import (
    SQLAlchemyTaskDependencyRepository,
)
from src.infrastructure.repositories.task_repository import SQLAlchemyTaskRepository

router = APIRouter(tags=["Software Company"])


def _to_project_response(p: SoftwareProject) -> SoftwareProjectResponse:
    return SoftwareProjectResponse(
        project_id=p.project_id,
        name=p.name,
        description=p.description,
        objective_id=p.objective_id,
        repository_path=p.repository_path,
        workspace_id=p.workspace_id,
        status=p.status.value,
        created_at=p.created_at,
    )


@router.post("/software-projects", response_model=SoftwareProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_software_project(
    payload: CreateSoftwareProjectRequest,
    db: AsyncSession = Depends(get_db),
) -> SoftwareProjectResponse:
    proj_repo = SQLAlchemySoftwareProjectRepository(db)
    req_repo = SQLAlchemySoftwareRequirementRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)
    dep_repo = SQLAlchemyTaskDependencyRepository(db)
    emp_repo = SQLAlchemyEmployeeRepository(db)
    asgn_repo = SQLAlchemyAssignmentRepository(db)
    obj_repo = SQLAlchemyObjectiveRepository(db)

    service = SoftwareProjectService(
        project_repo=proj_repo,
        req_repo=req_repo,
        task_repo=task_repo,
        dep_repo=dep_repo,
        employee_repo=emp_repo,
        assignment_repo=asgn_repo,
        objective_repo=obj_repo,
    )

    try:
        project = await service.create_software_project(
            objective_id=payload.objective_id,
            name=payload.name,
            description=payload.description,
            repository_path=payload.repository_path,
            workspace_id=payload.workspace_id,
        )
        await db.commit()
        return _to_project_response(project)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/software-projects/{project_id}", response_model=SoftwareProjectResponse)
async def get_software_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> SoftwareProjectResponse:
    proj_repo = SQLAlchemySoftwareProjectRepository(db)
    project = await proj_repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SoftwareProject '{project_id}' not found.")
    return _to_project_response(project)


@router.post("/software-projects/{project_id}/requirements", response_model=list[SoftwareRequirementResponse])
async def add_requirements(
    project_id: str,
    payload: AddRequirementsRequest,
    db: AsyncSession = Depends(get_db),
) -> list[SoftwareRequirementResponse]:
    proj_repo = SQLAlchemySoftwareProjectRepository(db)
    req_repo = SQLAlchemySoftwareRequirementRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)
    dep_repo = SQLAlchemyTaskDependencyRepository(db)
    emp_repo = SQLAlchemyEmployeeRepository(db)
    asgn_repo = SQLAlchemyAssignmentRepository(db)
    obj_repo = SQLAlchemyObjectiveRepository(db)

    service = SoftwareProjectService(
        project_repo=proj_repo,
        req_repo=req_repo,
        task_repo=task_repo,
        dep_repo=dep_repo,
        employee_repo=emp_repo,
        assignment_repo=asgn_repo,
        objective_repo=obj_repo,
    )

    try:
        reqs_data = [r.model_dump() for r in payload.requirements]
        reqs = await service.add_requirements(project_id=project_id, requirements_data=reqs_data)
        await db.commit()
        return [
            SoftwareRequirementResponse(
                requirement_id=r.requirement_id,
                project_id=r.project_id,
                title=r.title,
                description=r.description,
                acceptance_criteria=r.acceptance_criteria,
                priority=r.priority.value,
                status=r.status.value,
                created_at=r.created_at,
            )
            for r in reqs
        ]
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/software-projects/{project_id}/plan", response_model=EngineeringPlanResponse)
async def create_engineering_plan(
    project_id: str,
    payload: CreateEngineeringPlanRequest,
    db: AsyncSession = Depends(get_db),
) -> EngineeringPlanResponse:
    proj_repo = SQLAlchemySoftwareProjectRepository(db)
    req_repo = SQLAlchemySoftwareRequirementRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)
    dep_repo = SQLAlchemyTaskDependencyRepository(db)
    emp_repo = SQLAlchemyEmployeeRepository(db)
    asgn_repo = SQLAlchemyAssignmentRepository(db)
    obj_repo = SQLAlchemyObjectiveRepository(db)

    plan_repo = SQLAlchemyEngineeringPlanRepository(db)

    service = SoftwareProjectService(
        project_repo=proj_repo,
        req_repo=req_repo,
        task_repo=task_repo,
        dep_repo=dep_repo,
        employee_repo=emp_repo,
        assignment_repo=asgn_repo,
        objective_repo=obj_repo,
        plan_repo=plan_repo,
    )


    try:
        plan = await service.create_engineering_plan(
            project_id=project_id,
            manager_employee_id=payload.manager_employee_id,
            architecture_overview=payload.architecture_overview,
            tech_stack=payload.tech_stack,
        )
        await db.commit()
        return EngineeringPlanResponse(
            plan_id=plan.plan_id,
            project_id=plan.project_id,
            manager_employee_id=plan.manager_employee_id,
            architecture_overview=plan.architecture_overview,
            tech_stack=plan.tech_stack,
            task_ids=plan.task_ids,
            created_at=plan.created_at,
        )
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/software-projects/{project_id}/status")
async def get_project_status(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    proj_repo = SQLAlchemySoftwareProjectRepository(db)
    req_repo = SQLAlchemySoftwareRequirementRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)
    dep_repo = SQLAlchemyTaskDependencyRepository(db)
    emp_repo = SQLAlchemyEmployeeRepository(db)
    asgn_repo = SQLAlchemyAssignmentRepository(db)
    obj_repo = SQLAlchemyObjectiveRepository(db)
    change_repo = SQLAlchemyCodeChangeRepository(db)
    test_repo = SQLAlchemyTestRunRepository(db)
    defect_repo = SQLAlchemySoftwareDefectRepository(db)

    plan_repo = SQLAlchemyEngineeringPlanRepository(db)

    service = SoftwareProjectService(
        project_repo=proj_repo,
        req_repo=req_repo,
        task_repo=task_repo,
        dep_repo=dep_repo,
        employee_repo=emp_repo,
        assignment_repo=asgn_repo,
        objective_repo=obj_repo,
        plan_repo=plan_repo,
        change_repo=change_repo,
        test_repo=test_repo,
        defect_repo=defect_repo,
    )


    try:
        return await service.get_project_status(project_id)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.post("/code-changes", response_model=CodeChangeResponse, status_code=status.HTTP_201_CREATED)
async def submit_code_change(
    payload: SubmitCodeChangeRequest,
    db: AsyncSession = Depends(get_db),
) -> CodeChangeResponse:
    change_repo = SQLAlchemyCodeChangeRepository(db)
    review_repo = SQLAlchemyCodeReviewRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)

    service = CodeReviewService(change_repo=change_repo, review_repo=review_repo, task_repo=task_repo)

    change = await service.submit_code_change(
        project_id=payload.project_id,
        task_id=payload.task_id,
        author_employee_id=payload.author_employee_id,
        files_changed=payload.files_changed,
        diff_summary=payload.diff_summary,
        agent_run_id=payload.agent_run_id,
        workspace_id=payload.workspace_id,
        branch_name=payload.branch_name,
    )
    await db.commit()

    return CodeChangeResponse(
        change_id=change.change_id,
        project_id=change.project_id,
        task_id=change.task_id,
        author_employee_id=change.author_employee_id,
        branch_name=change.branch_name,
        files_changed=change.files_changed,
        status=change.status.value,
        commit_hash=change.commit_hash,
        created_at=change.created_at,
    )


@router.post("/code-changes/{change_id}/review-request", response_model=CodeReviewResponse)
async def request_code_review(
    change_id: str,
    payload: RequestCodeReviewRequest,
    db: AsyncSession = Depends(get_db),
) -> CodeReviewResponse:
    change_repo = SQLAlchemyCodeChangeRepository(db)
    review_repo = SQLAlchemyCodeReviewRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)

    service = CodeReviewService(change_repo=change_repo, review_repo=review_repo, task_repo=task_repo)

    try:
        review = await service.request_code_review(
            change_id=change_id,
            reviewer_employee_id=payload.reviewer_employee_id,
        )
        await db.commit()
        return CodeReviewResponse(
            review_id=review.review_id,
            change_id=review.change_id,
            reviewer_employee_id=review.reviewer_employee_id,
            status=review.status.value,
            findings=review.findings,
            recommendations=review.recommendations,
            created_at=review.created_at,
        )
    except UnauthorizedApprovalError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/code-reviews/{review_id}/findings", response_model=CodeReviewResponse)
async def submit_review_findings(
    review_id: str,
    payload: SubmitReviewFindingsRequest,
    db: AsyncSession = Depends(get_db),
) -> CodeReviewResponse:
    change_repo = SQLAlchemyCodeChangeRepository(db)
    review_repo = SQLAlchemyCodeReviewRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)

    service = CodeReviewService(change_repo=change_repo, review_repo=review_repo, task_repo=task_repo)

    try:
        rev_status = CodeReviewStatus[payload.status.upper()]
        review, _ = await service.submit_review_findings(
            review_id=review_id,
            status=rev_status,
            findings=payload.findings,
            recommendations=payload.recommendations,
            evidence_id=payload.evidence_id,
        )
        await db.commit()
        return CodeReviewResponse(
            review_id=review.review_id,
            change_id=review.change_id,
            reviewer_employee_id=review.reviewer_employee_id,
            status=review.status.value,
            findings=review.findings,
            recommendations=review.recommendations,
            created_at=review.created_at,
        )
    except UnauthorizedApprovalError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/test-runs", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def record_test_run(
    payload: RecordTestRunRequest,
    db: AsyncSession = Depends(get_db),
) -> TestRunResponse:
    test_repo = SQLAlchemyTestRunRepository(db)
    defect_repo = SQLAlchemySoftwareDefectRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)

    qa_service = QAService(test_repo=test_repo, defect_repo=defect_repo, task_repo=task_repo)

    test_run = await qa_service.record_test_run(
        project_id=payload.project_id,
        task_id=payload.task_id,
        worker_employee_id=payload.worker_employee_id,
        command=payload.command,
        exit_code=payload.exit_code,
        total_tests=payload.total_tests,
        passed_count=payload.passed_count,
        failed_count=payload.failed_count,
        skipped_count=payload.skipped_count,
        output_reference=payload.output_reference,
        agent_run_id=payload.agent_run_id,
        workspace_id=payload.workspace_id,
    )
    await db.commit()

    return TestRunResponse(
        test_run_id=test_run.test_run_id,
        project_id=test_run.project_id,
        task_id=test_run.task_id,
        worker_employee_id=test_run.worker_employee_id,
        command=test_run.command,
        exit_code=test_run.exit_code,
        total_tests=test_run.total_tests,
        passed_count=test_run.passed_count,
        failed_count=test_run.failed_count,
        status=test_run.status.value,
        created_at=test_run.created_at,
    )


@router.post("/software-projects/{project_id}/defects", response_model=SoftwareDefectResponse, status_code=status.HTTP_201_CREATED)
async def report_defect(
    project_id: str,
    payload: ReportDefectRequest,
    db: AsyncSession = Depends(get_db),
) -> SoftwareDefectResponse:
    test_repo = SQLAlchemyTestRunRepository(db)
    defect_repo = SQLAlchemySoftwareDefectRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)

    qa_service = QAService(test_repo=test_repo, defect_repo=defect_repo, task_repo=task_repo)

    sev_enum = DefectSeverity[payload.severity.upper()]
    defect, _ = await qa_service.report_defect(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        severity=sev_enum,
        reproduction_steps=payload.reproduction_steps,
        originating_task_id=payload.originating_task_id,
        assigned_employee_id=payload.assigned_employee_id,
    )
    await db.commit()

    return SoftwareDefectResponse(
        defect_id=defect.defect_id,
        project_id=defect.project_id,
        title=defect.title,
        severity=defect.severity.value,
        status=defect.status.value,
        fix_task_id=defect.fix_task_id,
        created_at=defect.created_at,
    )


@router.post("/software-projects/{project_id}/delivery-request", response_model=SoftwareDeliveryResponse, status_code=status.HTTP_201_CREATED)
async def request_delivery(
    project_id: str,
    payload: RequestDeliveryRequest,
    db: AsyncSession = Depends(get_db),
) -> SoftwareDeliveryResponse:
    delivery_repo = SQLAlchemySoftwareDeliveryRepository(db)
    proj_repo = SQLAlchemySoftwareProjectRepository(db)
    req_repo = SQLAlchemySoftwareRequirementRepository(db)
    change_repo = SQLAlchemyCodeChangeRepository(db)
    test_repo = SQLAlchemyTestRunRepository(db)
    defect_repo = SQLAlchemySoftwareDefectRepository(db)

    service = SoftwareDeliveryService(
        delivery_repo=delivery_repo,
        project_repo=proj_repo,
        req_repo=req_repo,
        change_repo=change_repo,
        test_repo=test_repo,
        defect_repo=defect_repo,
    )

    delivery = await service.request_delivery(
        project_id=project_id,
        requested_by_employee_id=payload.requested_by_employee_id,
        version=payload.version,
        commit_hash=payload.commit_hash,
    )
    await db.commit()

    return SoftwareDeliveryResponse(
        delivery_id=delivery.delivery_id,
        project_id=delivery.project_id,
        version=delivery.version,
        commit_hash=delivery.commit_hash,
        requested_by_employee_id=delivery.requested_by_employee_id,
        approved_by_employee_id=delivery.approved_by_employee_id,
        status=delivery.status.value,
        evidence_summary=delivery.evidence_summary,
        created_at=delivery.created_at,
    )


@router.post("/software-deliveries/{delivery_id}/approve", response_model=SoftwareDeliveryResponse)
async def approve_delivery(
    delivery_id: str,
    payload: ApproveDeliveryRequest,
    db: AsyncSession = Depends(get_db),
) -> SoftwareDeliveryResponse:
    delivery_repo = SQLAlchemySoftwareDeliveryRepository(db)
    proj_repo = SQLAlchemySoftwareProjectRepository(db)
    req_repo = SQLAlchemySoftwareRequirementRepository(db)
    change_repo = SQLAlchemyCodeChangeRepository(db)
    test_repo = SQLAlchemyTestRunRepository(db)
    defect_repo = SQLAlchemySoftwareDefectRepository(db)

    service = SoftwareDeliveryService(
        delivery_repo=delivery_repo,
        project_repo=proj_repo,
        req_repo=req_repo,
        change_repo=change_repo,
        test_repo=test_repo,
        defect_repo=defect_repo,
    )

    try:
        delivery = await service.approve_delivery(
            delivery_id=delivery_id,
            approved_by_employee_id=payload.approved_by_employee_id,
        )
        await db.commit()

        return SoftwareDeliveryResponse(
            delivery_id=delivery.delivery_id,
            project_id=delivery.project_id,
            version=delivery.version,
            commit_hash=delivery.commit_hash,
            requested_by_employee_id=delivery.requested_by_employee_id,
            approved_by_employee_id=delivery.approved_by_employee_id,
            status=delivery.status.value,
            evidence_summary=delivery.evidence_summary,
            created_at=delivery.created_at,
        )
    except UnauthorizedApprovalError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
