"""SQLAlchemy Repository for Team entities."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.team import Team, TeamMember
from src.infrastructure.models.team_model import TeamMemberModel, TeamModel


class SQLAlchemyTeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, team: Team) -> Team:
        model = await self.session.get(TeamModel, team.id)
        if model is None:
            model = TeamModel.from_domain(team)
            self.session.add(model)
        else:
            updated = TeamModel.from_domain(team)
            model.name = updated.name
            model.code = updated.code
            model.purpose = updated.purpose
            model.team_type = updated.team_type
            model.project_id = updated.project_id
            model.department_ids_json = updated.department_ids_json
            model.manager_id = updated.manager_id
            model.status = updated.status
            model.capabilities_json = updated.capabilities_json
            model.creation_reason = updated.creation_reason
            model.dissolved_at = updated.dissolved_at

            # Synchronize team members
            await self.session.execute(delete(TeamMemberModel).where(TeamMemberModel.team_id == team.id))
            model.members = [TeamMemberModel.from_domain(m) for m in team.members]

        await self.session.commit()
        return model.to_domain()

    async def get_by_id(self, team_id: str) -> Team | None:
        model = await self.session.get(TeamModel, team_id)
        return model.to_domain() if model else None

    async def get_by_code(self, code: str) -> Team | None:
        stmt = select(TeamModel).where(TeamModel.code == code)
        result = await self.session.execute(stmt)
        model = result.scalars().first()
        return model.to_domain() if model else None

    async def list_all(self) -> list[Team]:
        stmt = select(TeamModel)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.unique().scalars().all()]

    async def list_by_project(self, project_id: str) -> list[Team]:
        stmt = select(TeamModel).where(TeamModel.project_id == project_id)
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.unique().scalars().all()]

    async def list_by_employee(self, employee_id: str) -> list[Team]:
        stmt = (
            select(TeamModel)
            .join(TeamMemberModel)
            .where(TeamMemberModel.employee_id == employee_id, TeamMemberModel.removed_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return [m.to_domain() for m in result.unique().scalars().all()]
