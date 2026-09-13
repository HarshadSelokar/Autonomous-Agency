"""
SQLAlchemy Repository implementation for Meeting domain persistence.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.meeting import Meeting
from src.domain.repository import MeetingRepositoryInterface
from src.infrastructure.models.meeting_model import (
    MeetingModel,
    MeetingParticipantModel,
    meeting_domain_to_model,
    meeting_model_to_domain,
)


class SQLAlchemyMeetingRepository(MeetingRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, meeting: Meeting) -> Meeting:
        model = meeting_domain_to_model(meeting)
        merged = await self.session.merge(model)
        await self.session.flush()
        return meeting_model_to_domain(merged)

    async def get_by_id(self, meeting_id: str) -> Meeting | None:
        stmt = select(MeetingModel).where(MeetingModel.id == meeting_id)
        result = await self.session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return meeting_model_to_domain(model) if model else None

    async def list_all(self) -> list[Meeting]:
        stmt = select(MeetingModel).order_by(MeetingModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [meeting_model_to_domain(m) for m in models]

    async def list_by_participant(self, employee_id: str) -> list[Meeting]:
        stmt = (
            select(MeetingModel)
            .join(MeetingParticipantModel, MeetingModel.id == MeetingParticipantModel.meeting_id)
            .where(MeetingParticipantModel.employee_id == employee_id)
            .order_by(MeetingModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.unique().scalars().all()
        return [meeting_model_to_domain(m) for m in models]
