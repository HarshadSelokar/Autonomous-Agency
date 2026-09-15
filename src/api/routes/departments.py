"""FastAPI Router for Department Lifecycle and Health Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.department import (
    AssignDepartmentManagerSchema,
    CreateDepartmentSchema,
    DepartmentHealthReportSchema,
    DepartmentResponseSchema,
    UpdateDepartmentStatusSchema,
)
from src.application.department_service import DepartmentService
from src.domain.department import DepartmentStatus
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository

router = APIRouter(prefix="/departments", tags=["Departments"])


def get_department_service(session: AsyncSession = Depends(get_db_session)) -> DepartmentService:
    repo = SQLAlchemyDepartmentRepository(session)
    return DepartmentService(department_repository=repo)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DepartmentResponseSchema)
async def create_department(
    payload: CreateDepartmentSchema,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponseSchema:
    dept = await service.create_department(
        department_id=payload.id,
        name=payload.name,
        code=payload.code,
        description=payload.description,
        purpose=payload.purpose,
        parent_department_id=payload.parent_department_id,
        capabilities=payload.capabilities,
        responsibilities=payload.responsibilities,
    )
    return _map_dept_response(dept)


@router.get("", response_model=List[DepartmentResponseSchema])
async def list_departments(
    service: DepartmentService = Depends(get_department_service),
) -> List[DepartmentResponseSchema]:
    depts = await service.list_departments()
    return [_map_dept_response(d) for d in depts]


@router.post("/bootstrap", response_model=List[DepartmentResponseSchema])
async def bootstrap_departments(
    service: DepartmentService = Depends(get_department_service),
) -> List[DepartmentResponseSchema]:
    depts = await service.bootstrap_enterprise_departments()
    return [_map_dept_response(d) for d in depts]


@router.get("/{department_id}", response_model=DepartmentResponseSchema)
async def get_department(
    department_id: str,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponseSchema:
    dept = await service.get_department(department_id)
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department '{department_id}' not found.")
    return _map_dept_response(dept)


@router.post("/{department_id}/status", response_model=DepartmentResponseSchema)
async def update_department_status(
    department_id: str,
    payload: UpdateDepartmentStatusSchema,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponseSchema:
    try:
        new_status = DepartmentStatus(payload.status)
        dept = await service.update_status(department_id, new_status, reason=payload.reason)
        return _map_dept_response(dept)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{department_id}/manager", response_model=DepartmentResponseSchema)
async def assign_department_manager(
    department_id: str,
    payload: AssignDepartmentManagerSchema,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentResponseSchema:
    try:
        dept = await service.assign_manager(department_id, payload.manager_employee_id)
        return _map_dept_response(dept)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{department_id}/health", response_model=DepartmentHealthReportSchema)
async def get_department_health(
    department_id: str,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentHealthReportSchema:
    try:
        report = await service.evaluate_department_health(department_id)
        return DepartmentHealthReportSchema(
            department_id=report.department_id,
            health=report.health.value if hasattr(report.health, "value") else str(report.health),
            reason=report.reason,
            downstream_blocked_count=report.downstream_blocked_count,
            active_tasks=report.metrics.active_tasks,
            blocked_tasks=report.metrics.blocked_tasks,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def _map_dept_response(dept) -> DepartmentResponseSchema:
    return DepartmentResponseSchema(
        id=dept.id,
        name=dept.name,
        code=dept.code,
        description=dept.description,
        status=dept.status.value if hasattr(dept.status, "value") else str(dept.status),
        purpose=dept.purpose,
        manager_employee_id=dept.manager_employee_id,
        parent_department_id=dept.parent_department_id,
        capabilities=dept.capabilities,
        responsibilities=dept.responsibilities,
        created_at=str(dept.created_at),
        updated_at=str(dept.updated_at),
    )
