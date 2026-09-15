"""SQLAlchemy implementation of DepartmentRepositoryInterface for Phase 14."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.department import Department
from src.domain.repository import DepartmentRepositoryInterface
from src.infrastructure.models.department_model import (
    DepartmentModel,
    department_domain_to_model,
    department_model_to_domain,
)


class SQLAlchemyDepartmentRepository(DepartmentRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, department: Department) -> Department:
        """Save or update a Department entity."""
        model = await self.session.get(DepartmentModel, department.id)
        if model is None:
            model = department_domain_to_model(department)
            self.session.add(model)
        else:
            updated_model = department_domain_to_model(department)
            model.name = updated_model.name
            model.code = updated_model.code
            model.description = updated_model.description
            model.status = updated_model.status
            model.purpose = updated_model.purpose
            model.manager_employee_id = updated_model.manager_employee_id
            model.parent_department_id = updated_model.parent_department_id
            model.capabilities_json = updated_model.capabilities_json
            model.responsibilities_json = updated_model.responsibilities_json
            model.policies_json = updated_model.policies_json
            model.updated_at = updated_model.updated_at

        await self.session.flush()
        return department_model_to_domain(model)

    async def get_by_id(self, department_id: str) -> Department | None:
        """Find a Department by ID."""
        model = await self.session.get(DepartmentModel, department_id)
        if model is None:
            return None
        return department_model_to_domain(model)

    async def list_all(self) -> list[Department]:
        """List all Department entities."""
        stmt = select(DepartmentModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [department_model_to_domain(m) for m in models]
