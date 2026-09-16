"""SQLAlchemy Repositories for Cross-Department Requests, Handoffs, and Service Contracts."""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.cross_department import (
    DepartmentHandoff,
    DepartmentRequest,
)
from src.infrastructure.models.cross_department_model import (
    DepartmentHandoffModel,
    DepartmentRequestModel,
    department_handoff_domain_to_model,
    department_handoff_model_to_domain,
    department_request_domain_to_model,
    department_request_model_to_domain,
)


class SQLAlchemyDepartmentRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, request: DepartmentRequest) -> DepartmentRequest:
        model = await self.session.get(DepartmentRequestModel, request.request_id)
        if model is None:
            model = department_request_domain_to_model(request)
            self.session.add(model)
        else:
            updated = department_request_domain_to_model(request)
            model.status = updated.status
            model.delivery_owner_employee_id = updated.delivery_owner_employee_id
            model.rejection_reason = updated.rejection_reason
            model.priority = updated.priority
            model.updated_at = updated.updated_at

        await self.session.flush()
        return department_request_model_to_domain(model)

    async def get_by_id(self, request_id: str) -> DepartmentRequest | None:
        model = await self.session.get(DepartmentRequestModel, request_id)
        if model is None:
            return None
        return department_request_model_to_domain(model)

    async def list_by_department(
        self, department_id: str, as_requester: bool = True
    ) -> list[DepartmentRequest]:
        stmt = select(DepartmentRequestModel)
        if as_requester:
            stmt = stmt.where(DepartmentRequestModel.requester_department_id == department_id)
        else:
            stmt = stmt.where(DepartmentRequestModel.receiving_department_id == department_id)

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [department_request_model_to_domain(m) for m in models]

    async def list_all(self) -> list[DepartmentRequest]:
        stmt = select(DepartmentRequestModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [department_request_model_to_domain(m) for m in models]


class SQLAlchemyDepartmentHandoffRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, handoff: DepartmentHandoff) -> DepartmentHandoff:
        model = await self.session.get(DepartmentHandoffModel, handoff.handoff_id)
        if model is None:
            model = department_handoff_domain_to_model(handoff)
            self.session.add(model)
        else:
            updated = department_handoff_domain_to_model(handoff)
            model.status = updated.status
            model.is_verified = updated.is_verified
            model.verification_id = updated.verification_id
            model.rejection_reason = updated.rejection_reason

        await self.session.flush()
        return department_handoff_model_to_domain(model)

    async def get_by_id(self, handoff_id: str) -> DepartmentHandoff | None:
        model = await self.session.get(DepartmentHandoffModel, handoff_id)
        if model is None:
            return None
        return department_handoff_model_to_domain(model)

    async def get_by_request_id(self, request_id: str) -> DepartmentHandoff | None:
        stmt = select(DepartmentHandoffModel).where(DepartmentHandoffModel.request_id == request_id)
        result = await self.session.execute(stmt)
        model = result.scalars().first()
        if model is None:
            return None
        return department_handoff_model_to_domain(model)
