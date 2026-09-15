"""FastAPI Routes for Phase 14 Cross-Department Requests."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.department import (
    DepartmentRequestAcceptSchema,
    DepartmentRequestCreateSchema,
    DepartmentRequestDeliverSchema,
    DepartmentRequestRejectSchema,
    DepartmentRequestResponseSchema,
    DepartmentRequestVerifySchema,
)
from src.application.department_service import DepartmentService
from src.domain.department import DepartmentRequestPriority
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository

router = APIRouter(tags=["Cross-Department Collaboration"])


def get_department_service(session: AsyncSession = Depends(get_db_session)) -> DepartmentService:
    repo = SQLAlchemyDepartmentRepository(session)
    return DepartmentService(department_repository=repo)


@router.post("/departments/{department_id}/requests", status_code=status.HTTP_201_CREATED, response_model=DepartmentRequestResponseSchema)
async def create_department_request(
    department_id: str,
    payload: DepartmentRequestCreateSchema,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentRequestResponseSchema:
    try:
        prio = DepartmentRequestPriority(payload.priority)
        req = await service.create_request(
            requester_department_id=department_id,
            receiving_department_id=payload.receiving_department_id,
            requester_employee_id=payload.requester_employee_id,
            purpose=payload.purpose,
            requested_outcome=payload.requested_outcome,
            priority=prio,
            required_capabilities=payload.required_capabilities,
            related_objective_id=payload.related_objective_id,
            related_project_id=payload.related_project_id,
        )
        return DepartmentRequestResponseSchema(
            request_id=req.request_id,
            requester_department_id=req.requester_department_id,
            receiving_department_id=req.receiving_department_id,
            requester_employee_id=req.requester_employee_id,
            purpose=req.purpose,
            requested_outcome=req.requested_outcome,
            priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
            status=req.status.value if hasattr(req.status, "value") else str(req.status),
            accountable_manager_id=req.accountable_manager_id,
            delivery_owner_employee_id=req.delivery_owner_employee_id,
            rejection_reason=req.rejection_reason,
            created_at=str(req.created_at),
            updated_at=str(req.updated_at),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/departments/{department_id}/requests", response_model=List[DepartmentRequestResponseSchema])
async def list_department_requests(
    department_id: str,
    as_requester: bool = True,
    service: DepartmentService = Depends(get_department_service),
) -> List[DepartmentRequestResponseSchema]:
    if not service.department_repo:
        return []
    requests = await service.department_repo.list_requests(department_id, as_requester=as_requester)
    return [
        DepartmentRequestResponseSchema(
            request_id=req.request_id,
            requester_department_id=req.requester_department_id,
            receiving_department_id=req.receiving_department_id,
            requester_employee_id=req.requester_employee_id,
            purpose=req.purpose,
            requested_outcome=req.requested_outcome,
            priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
            status=req.status.value if hasattr(req.status, "value") else str(req.status),
            accountable_manager_id=req.accountable_manager_id,
            delivery_owner_employee_id=req.delivery_owner_employee_id,
            rejection_reason=req.rejection_reason,
            created_at=str(req.created_at),
            updated_at=str(req.updated_at),
        )
        for req in requests
    ]


@router.get("/department-requests/{request_id}", response_model=DepartmentRequestResponseSchema)
async def get_department_request(
    request_id: str,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentRequestResponseSchema:
    if not service.department_repo:
        raise HTTPException(status_code=404, detail="Department repository uninitialized")

    req = await service.department_repo.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail=f"Department request not found: {request_id}")

    return DepartmentRequestResponseSchema(
        request_id=req.request_id,
        requester_department_id=req.requester_department_id,
        receiving_department_id=req.receiving_department_id,
        requester_employee_id=req.requester_employee_id,
        purpose=req.purpose,
        requested_outcome=req.requested_outcome,
        priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
        status=req.status.value if hasattr(req.status, "value") else str(req.status),
        accountable_manager_id=req.accountable_manager_id,
        delivery_owner_employee_id=req.delivery_owner_employee_id,
        rejection_reason=req.rejection_reason,
        created_at=str(req.created_at),
        updated_at=str(req.updated_at),
    )


@router.post("/department-requests/{request_id}/accept", response_model=DepartmentRequestResponseSchema)
async def accept_department_request(
    request_id: str,
    payload: DepartmentRequestAcceptSchema,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentRequestResponseSchema:
    try:
        req = await service.accept_request(
            request_id=request_id,
            receiving_manager_id=payload.receiving_manager_id,
            delivery_owner_employee_id=payload.delivery_owner_employee_id,
        )
        return DepartmentRequestResponseSchema(
            request_id=req.request_id,
            requester_department_id=req.requester_department_id,
            receiving_department_id=req.receiving_department_id,
            requester_employee_id=req.requester_employee_id,
            purpose=req.purpose,
            requested_outcome=req.requested_outcome,
            priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
            status=req.status.value if hasattr(req.status, "value") else str(req.status),
            accountable_manager_id=req.accountable_manager_id,
            delivery_owner_employee_id=req.delivery_owner_employee_id,
            rejection_reason=req.rejection_reason,
            created_at=str(req.created_at),
            updated_at=str(req.updated_at),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/department-requests/{request_id}/reject", response_model=DepartmentRequestResponseSchema)
async def reject_department_request(
    request_id: str,
    payload: DepartmentRequestRejectSchema,
    service: DepartmentService = Depends(get_department_service),
) -> DepartmentRequestResponseSchema:
    try:
        req = await service.reject_request(
            request_id=request_id,
            rejector_actor_id=payload.rejector_actor_id,
            reason=payload.reason,
        )
        return DepartmentRequestResponseSchema(
            request_id=req.request_id,
            requester_department_id=req.requester_department_id,
            receiving_department_id=req.receiving_department_id,
            requester_employee_id=req.requester_employee_id,
            purpose=req.purpose,
            requested_outcome=req.requested_outcome,
            priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
            status=req.status.value if hasattr(req.status, "value") else str(req.status),
            accountable_manager_id=req.accountable_manager_id,
            delivery_owner_employee_id=req.delivery_owner_employee_id,
            rejection_reason=req.rejection_reason,
            created_at=str(req.created_at),
            updated_at=str(req.updated_at),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
