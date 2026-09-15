"""FastAPI Routes for Phase 14 Departments."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.department import (
    DepartmentCreateSchema,
    DepartmentMetricsResponseSchema,
    DepartmentResponseSchema,
    DepartmentUpdateSchema,
)
from src.application.department_service import DepartmentService
from src.domain.department import DepartmentStatus
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository

router = APIRouter(prefix="/departments", tags=["Departments"])


def get_department_service(session: AsyncSession = Depends(get_db_session)) -> DepartmentService:
    repo = SQLAlchemyDepartmentRepository(session)
    return DepartmentService(department_repository=repo)


@router.get("", response_model=List[DepartmentResponseSchema])
async def list_departments(
    service: DepartmentService = Depends(get_department_service),
) -> List[DepartmentResponseSchema]:
    if not service.department_repo:
        return []
    depts = await service.department_repo.list_all()
    return [
        DepartmentResponseSchema(
            id=d.id,
            name=d.name,
            code=d.code,
            description=d.description,
            purpose=d.purpose,
            status=d.status.value if hasattr(d.status, "value") else str(d.status),
            responsibilities=d.responsibilities,
            capabilities=d.capabilities,
            manager_employee_id=d.manager_employee_id,
            parent_department_id=d.parent_department_id,
            created_at=str(d.created_at),
            updated_at=str(d.updated_at),
        )
        for d in depts
    ]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DepartmentResponseSchema)
async def create_department(
    payload: DepartmentCreateSchema,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponseSchema:
    dept = await service.register_department(
        id=payload.id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        purpose=payload.purpose,
        responsibilities=payload.responsibilities,
        capabilities=payload.capabilities,
        manager_employee_id=payload.manager_employee_id,
        parent_department_id=payload.parent_department_id,
    )
    return DepartmentResponseSchema(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        purpose=dept.purpose,
        status=dept.status.value if hasattr(dept.status, "value") else str(dept.status),
        responsibilities=dept.responsibilities,
        capabilities=dept.capabilities,
        manager_employee_id=dept.manager_employee_id,
        parent_department_id=dept.parent_department_id,
        created_at=str(dept.created_at),
        updated_at=str(dept.updated_at),
    )


@router.get("/{department_id}", response_model=DepartmentResponseSchema)
async def get_department(
    department_id: str,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponseSchema:
    if not service.department_repo:
        raise HTTPException(status_code=404, detail="Department repository uninitialized")

    dept = await service.department_repo.get_by_id(department_id)
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department not found: {department_id}")

    return DepartmentResponseSchema(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        purpose=dept.purpose,
        status=dept.status.value if hasattr(dept.status, "value") else str(dept.status),
        responsibilities=dept.responsibilities,
        capabilities=dept.capabilities,
        manager_employee_id=dept.manager_employee_id,
        parent_department_id=dept.parent_department_id,
        created_at=str(dept.created_at),
        updated_at=str(dept.updated_at),
    )


@router.patch("/{department_id}", response_model=DepartmentResponseSchema)
async def update_department(
    department_id: str,
    payload: DepartmentUpdateSchema,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponseSchema:
    if payload.status:
        try:
            status_enum = DepartmentStatus(payload.status)
            await service.update_department_status(department_id, status_enum)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if payload.manager_employee_id:
        await service.assign_manager(department_id, payload.manager_employee_id)

    dept = await service.department_repo.get_by_id(department_id)
    return DepartmentResponseSchema(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        purpose=dept.purpose,
        status=dept.status.value if hasattr(dept.status, "value") else str(dept.status),
        responsibilities=dept.responsibilities,
        capabilities=dept.capabilities,
        manager_employee_id=dept.manager_employee_id,
        parent_department_id=dept.parent_department_id,
        created_at=str(dept.created_at),
        updated_at=str(dept.updated_at),
    )


@router.get("/{department_id}/health", response_model=DepartmentMetricsResponseSchema)
async def get_department_health(
    department_id: str,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentMetricsResponseSchema:
    metrics = await service.calculate_department_health(department_id)
    return DepartmentMetricsResponseSchema(
        department_id=metrics.department_id,
        active_task_count=metrics.active_task_count,
        completed_task_count=metrics.completed_task_count,
        blocked_task_count=metrics.blocked_task_count,
        incoming_request_count=metrics.incoming_request_count,
        outgoing_request_count=metrics.outgoing_request_count,
        verification_failure_count=metrics.verification_failure_count,
        recovery_attempt_count=metrics.recovery_attempt_count,
        escalation_count=metrics.escalation_count,
        health=metrics.health.value if hasattr(metrics.health, "value") else str(metrics.health),
        updated_at=str(metrics.updated_at),
    )
