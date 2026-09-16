"""
FastAPI Routes for Phase 6 Meeting Management.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.meeting_schemas import (
    AddAgendaItemRequest,
    AddParticipantRequest,
    CreateMeetingRequest,
    MeetingResponse,
    ScheduleMeetingRequest,
)
from src.application.meeting_context_builder import MeetingAccessDeniedError, MeetingContextBuilder
from src.application.meeting_scheduling_service import MeetingSchedulingService
from src.domain.exceptions import EmployeeNotFoundError, ObjectiveValidationError
from src.domain.meeting import (
    MeetingPurpose,
    MeetingStatus,
    ParticipantRole,
)
from src.infrastructure.database import get_db
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.repositories.meeting_repository import SQLAlchemyMeetingRepository

router = APIRouter(prefix="/meetings", tags=["Meetings"])


def _to_meeting_response(meeting: Any) -> MeetingResponse:
    return MeetingResponse(
        id=meeting.id,
        title=meeting.title,
        purpose=meeting.purpose.value,
        status=meeting.status.value,
        organizer_employee_id=meeting.organizer_employee_id,
        scheduled_start=meeting.scheduled_start,
        scheduled_end=meeting.scheduled_end,
        actual_start=meeting.actual_start,
        actual_end=meeting.actual_end,
        conversation_id=meeting.conversation_id,
        objective_id=meeting.objective_id,
        plan_id=meeting.plan_id,
        task_id=meeting.task_id,
        participant_count=len(meeting.participants),
        agenda_item_count=len(meeting.agenda_items),
        created_at=meeting.created_at,
    )


@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: CreateMeetingRequest,
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    meeting_repo = SQLAlchemyMeetingRepository(db)
    employee_repo = SQLAlchemyEmployeeRepository(db)
    service = MeetingSchedulingService(meeting_repo=meeting_repo, employee_repo=employee_repo)

    try:
        meeting_id = f"mtg-{uuid.uuid4().hex[:8]}"
        purpose_enum = MeetingPurpose(payload.purpose.upper())
        meeting = await service.create_meeting(
            meeting_id=meeting_id,
            title=payload.title,
            purpose=purpose_enum,
            organizer_employee_id=payload.organizer_employee_id,
            participant_ids=payload.participant_ids,
            objective_id=payload.objective_id,
            plan_id=payload.plan_id,
            task_id=payload.task_id,
        )
        await db.commit()
        return _to_meeting_response(meeting)
    except (EmployeeNotFoundError, ObjectiveValidationError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("", response_model=list[MeetingResponse])
async def list_meetings(
    db: AsyncSession = Depends(get_db),
) -> list[MeetingResponse]:
    repo = SQLAlchemyMeetingRepository(db)
    meetings = await repo.list_all()
    return [_to_meeting_response(m) for m in meetings]


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    repo = SQLAlchemyMeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Meeting '{meeting_id}' not found.")
    return _to_meeting_response(meeting)


@router.post("/{meeting_id}/schedule", response_model=MeetingResponse)
async def schedule_meeting(
    meeting_id: str,
    payload: ScheduleMeetingRequest,
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    meeting_repo = SQLAlchemyMeetingRepository(db)
    employee_repo = SQLAlchemyEmployeeRepository(db)
    service = MeetingSchedulingService(meeting_repo=meeting_repo, employee_repo=employee_repo)

    try:
        scheduled = await service.schedule_meeting(
            meeting_id=meeting_id,
            scheduled_start=payload.scheduled_start,
            scheduled_end=payload.scheduled_end,
        )
        await db.commit()
        return _to_meeting_response(scheduled)
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{meeting_id}/participants", response_model=MeetingResponse)
async def add_participant(
    meeting_id: str,
    payload: AddParticipantRequest,
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    repo = SQLAlchemyMeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Meeting '{meeting_id}' not found.")

    try:
        role_enum = ParticipantRole(payload.role.upper())
        meeting.add_participant(employee_id=payload.employee_id, role=role_enum, agent_id=payload.agent_id)
        saved = await repo.save(meeting)
        return _to_meeting_response(saved)
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{meeting_id}/agenda", response_model=MeetingResponse)
async def add_agenda_item(
    meeting_id: str,
    payload: AddAgendaItemRequest,
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    repo = SQLAlchemyMeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Meeting '{meeting_id}' not found.")

    try:
        item_id = f"ag-{uuid.uuid4().hex[:6]}"
        meeting.add_agenda_item(
            item_id=item_id,
            title=payload.title,
            description=payload.description,
            owner_employee_id=payload.owner_employee_id,
            duration_minutes=payload.duration_minutes,
            task_id=payload.task_id,
            objective_id=payload.objective_id,
        )
        saved = await repo.save(meeting)
        return _to_meeting_response(saved)
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{meeting_id}/start", response_model=MeetingResponse)
async def start_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    repo = SQLAlchemyMeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Meeting '{meeting_id}' not found.")

    try:
        meeting.transition_to(MeetingStatus.STARTING)
        meeting.transition_to(MeetingStatus.IN_PROGRESS)
        saved = await repo.save(meeting)
        await db.commit()
        return _to_meeting_response(saved)
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{meeting_id}/end", response_model=MeetingResponse)
async def end_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
) -> MeetingResponse:
    repo = SQLAlchemyMeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Meeting '{meeting_id}' not found.")

    try:
        meeting.transition_to(MeetingStatus.ENDED)
        saved = await repo.save(meeting)
        await db.commit()
        return _to_meeting_response(saved)
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/{meeting_id}/context")
async def get_meeting_context(
    meeting_id: str,
    requesting_employee_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    meeting_repo = SQLAlchemyMeetingRepository(db)
    builder = MeetingContextBuilder(meeting_repo=meeting_repo)

    try:
        return await builder.build_context(meeting_id=meeting_id, requesting_employee_id=requesting_employee_id)
    except MeetingAccessDeniedError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err))
    except ObjectiveValidationError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
