"""
Registers a dev project's team in the company's employee and agent tables, so the rest of
the platform (office views, org endpoints) knows these agents exist.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.agent import Agent, ModelConfiguration
from src.domain.dev_project import DevProject, TeamRole
from src.domain.employee import Employee, EmployeeStatus
from src.infrastructure.repositories.agent_repository import SQLAlchemyAgentRepository
from src.infrastructure.repositories.employee_repository import SQLAlchemyEmployeeRepository
from src.infrastructure.tenant_context import _current_tenant_id

TITLES = {
    TeamRole.MANAGER: "Engineering Manager",
    TeamRole.DEVELOPER: "Software Developer",
    TeamRole.QA: "QA Engineer",
    TeamRole.REVIEWER: "Code Reviewer",
}


class StudioTeamDirectory:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def register(self, project: DevProject, provider: str, model: str) -> None:
        """Create or update one Agent and one Employee per team member (idempotent)."""
        manager_id = project.member(TeamRole.MANAGER).id
        # Bind the project's tenant so the rows are stamped and looked up within it,
        # even when this runs outside a request (for example on auto-resume)
        token = _current_tenant_id.set(project.tenant_id)
        try:
            await self._register(project, provider, model, manager_id)
        finally:
            _current_tenant_id.reset(token)

    async def _register(self, project: DevProject, provider: str, model: str, manager_id: str) -> None:
        async with self.session_factory() as session:
            agents = SQLAlchemyAgentRepository(session)
            employees = SQLAlchemyEmployeeRepository(session)
            for member in project.team():
                agent = Agent(
                    id=member.id,
                    name=member.name,
                    role=member.role.value.lower(),
                    description=f"{TITLES[member.role]} on studio project '{project.name}'.",
                    manager_id=None if member.id == manager_id else manager_id,
                    model_configuration=ModelConfiguration(provider=provider, model=model or "default"),
                    metadata={"studio_project_id": project.id},
                )
                await agents.save(agent)
                await employees.save(
                    Employee(
                        id=member.id,
                        employee_code=member.id,
                        name=member.name,
                        title=TITLES[member.role],
                        role=member.role.value.lower(),
                        agent_id=member.id,
                        manager_id=None if member.id == manager_id else manager_id,
                        status=EmployeeStatus.ACTIVE,
                        metadata={"studio_project_id": project.id},
                    )
                )
            await session.commit()
