"""FastAPI Router for Cross-Department Requests and Handoff Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.department import (
    AcceptDepartmentRequestSchema,
    CreateDepartmentRequestSchema,
    DepartmentHandoffResponseSchema,
    DepartmentRequestResponseSchema,
    RejectDepartmentRequestSchema,
    SubmitDepartmentHandoffSchema,
    VerifyDepartmentHandoffSchema,
)
from src.application.cross_department_service import CrossDepartmentService
from src.domain.department import DepartmentPriority
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.cross_department_repository import (
    SQLAlchemyDepartmentHandoffRepository,
    SQLAlchemyDepartmentRequestRepository,
)
from src.infrastructure.repositories.department_repository import SQLAlchemyDepartmentRepository

router = APIRouter(prefix="/department-requests", tags=["Cross-Department Requests"])


def get_cross_department_service(
    session: AsyncSession = Depends(get_db_session),
) -> CrossDepartmentService:
    dept_repo = SQLAlchemyDepartmentRepository(session)
    req_repo = SQLAlchemyDepartmentRequestRepository(session)
    handoff_repo = SQLAlchemyDepartmentHandoffRepository(session)
    return CrossDepartmentService(
        department_repository=dept_repo,
        request_repository=req_repo,
        handoff_repository=handoff_repo,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DepartmentRequestResponseSchema)
async def submit_request(
    payload: CreateDepartmentRequestSchema,
    service: CrossDepartmentService = Depends(get_cross_department_service),
) -> DepartmentRequestResponseSchema:
    try:
        priority = DepartmentPriority(payload.priority)
        req = await service.submit_request(
            requester_department_id=payload.requester_department_id,
            receiving_department_id=payload.receiving_department_id,
            requester_employee_id=payload.requester_employee_id,
            purpose=payload.purpose,
            requested_outcome=payload.requested_outcome,
            priority=priority,
            required_capabilities=payload.required_capabilities,
            related_objective_id=payload.related_objective_id,
            related_project_id=payload.related_project_id,
        )
        return _map_request_response(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{request_id}", response_model=DepartmentRequestResponseSchema)
async def get_request(
    request_id: str,
    service: CrossDepartmentService = Depends(get_cross_department_service),
) -> DepartmentRequestResponseSchema:
    req = await service.req_repo.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail=f"Request '{request_id}' not found.")
    return _map_request_response(req)


@router.post("/{request_id}/accept", response_model=DepartmentRequestResponseSchema)
async def accept_request(
    request_id: str,
    payload: AcceptDepartmentRequestSchema,
    service: CrossDepartmentService = Depends(get_cross_department_service),
) -> DepartmentRequestResponseSchema:
    try:
        req = await service.accept_request(
            request_id=request_id,
            receiving_manager_id=payload.receiving_manager_id,
            delivery_owner_employee_id=payload.delivery_owner_employee_id,
        )
        return _map_request_response(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/reject", response_model=DepartmentRequestResponseSchema)
async def reject_request(
    request_id: str,
    payload: RejectDepartmentRequestSchema,
    service: CrossDepartmentService = Depends(get_cross_department_service),
) -> DepartmentRequestResponseSchema:
    try:
        req = await service.reject_request(
            request_id=request_id,
            receiving_manager_id=payload.receiving_manager_id,
            reason=payload.reason,
        )
        return _map_request_response(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/handoff", status_code=status.HTTP_201_CREATED, response_model=DepartmentHandoffResponseSchema)
async def submit_handoff(
    request_id: str,
    payload: SubmitDepartmentHandoffSchema,
    service: CrossDepartmentService = Depends(get_cross_department_service),
) -> DepartmentHandoffResponseSchema:
    try:
        handoff = await service.submit_handoff(
            request_id=request_id,
            sender_employee_id=payload.sender_employee_id,
            expected_outcome=payload.expected_outcome,
            artifact_ids=payload.artifact_ids,
            evidence_ids=payload.evidence_ids,
            acceptance_criteria=payload.acceptance_criteria,
        )
        return _map_handoff_response(handoff)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/handoffs/{handoff_id}/verify", response_model=DepartmentHandoffResponseSchema)
async def verify_handoff(
    handoff_id: str,
    payload: VerifyDepartmentHandoffSchema,
    service: CrossDepartmentService = Depends(get_cross_department_service),
) -> DepartmentHandoffResponseSchema:
    try:
        handoff = await service.verify_handoff(
            handoff_id=handoff_id,
            verifier_employee_id=payload.verifier_employee_id,
            is_approved=payload.is_approved,
            reason=payload.reason,
        )
        return _map_handoff_response(handoff)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _map_request_response(req) -> DepartmentRequestResponseSchema:
    return DepartmentRequestResponseSchema(
        request_id=req.request_id,
        requester_department_id=req.requester_department_id,
        receiving_department_id=req.receiving_department_id,
        requester_employee_id=req.requester_employee_id,
        receiving_manager_id=req.receiving_manager_id,
        delivery_owner_employee_id=req.delivery_owner_employee_id,
        purpose=req.purpose,
        requested_outcome=req.requested_outcome,
        priority=req.priority.value if hasattr(req.priority, "value") else str(req.priority),
        status=req.status.value if hasattr(req.status, "value") else str(req.status),
        rejection_reason=req.rejection_reason,
        created_at=str(req.created_at),
        updated_at=str(req.updated_at),
    )


def _map_handoff_response(h) -> DepartmentHandoffResponseSchema:
    return DepartmentHandoffResponseSchema(
        handoff_id=h.handoff_id,
        request_id=h.request_id,
        sender_department_id=h.sender_department_id,
        receiver_department_id=h.receiver_department_id,
        sender_employee_id=h.sender_employee_id,
        expected_outcome=h.expected_outcome,
        status=h.status.value if hasattr(h.status, "value") else str(h.status),
        is_verified=h.is_verified,
        rejection_reason=h.rejection_reason,
        created_at=str(h.created_at),
    )
