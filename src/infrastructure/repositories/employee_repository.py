"""
SQLAlchemy implementation of EmployeeRepositoryInterface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.employee import Employee
from src.domain.repository import EmployeeRepositoryInterface
from src.infrastructure.models.employee_model import (
    EmployeeModel,
    employee_domain_to_model,
    employee_model_to_domain,
)


class SQLAlchemyEmployeeRepository(EmployeeRepositoryInterface):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, employee: Employee) -> Employee:
        """Save or update an Employee entity."""
        model = await self.session.get(EmployeeModel, employee.id)
        if model is None:
            model = employee_domain_to_model(employee)
            self.session.add(model)
        else:
            updated_model = employee_domain_to_model(employee)
            model.employee_code = updated_model.employee_code
            model.name = updated_model.name
            model.title = updated_model.title
            model.role = updated_model.role
            model.agent_id = updated_model.agent_id
            model.department_id = updated_model.department_id
            model.manager_id = updated_model.manager_id
            model.responsibilities = updated_model.responsibilities
            model.skills_json = updated_model.skills_json
            model.capabilities_json = updated_model.capabilities_json
            model.status = updated_model.status
            model.metadata_json = updated_model.metadata_json
            model.updated_at = updated_model.updated_at

        await self.session.flush()
        return employee_model_to_domain(model)

    async def get_by_id(self, employee_id: str) -> Employee | None:
        """Find an Employee by ID."""
        model = await self.session.get(EmployeeModel, employee_id)
        if model is None:
            return None
        return employee_model_to_domain(model)

    async def get_by_code(self, employee_code: str) -> Employee | None:
        """Find an Employee by employee_code."""
        stmt = select(EmployeeModel).where(EmployeeModel.employee_code == employee_code)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return employee_model_to_domain(model)

    async def list_all(self) -> list[Employee]:
        """List all Employee entities."""
        stmt = select(EmployeeModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [employee_model_to_domain(m) for m in models]

    async def list_by_department_id(self, department_id: str) -> list[Employee]:
        """List all Employees assigned to a specific department."""
        stmt = select(EmployeeModel).where(EmployeeModel.department_id == department_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [employee_model_to_domain(m) for m in models]

    async def delete(self, employee_id: str) -> bool:
        """Delete an Employee by ID."""
        model = await self.session.get(EmployeeModel, employee_id)
        if model is None:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True
