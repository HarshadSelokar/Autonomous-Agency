"""
Multi-Company REST API Endpoints for Phase 25.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db_session
from src.infrastructure.repositories.company_repository import SQLAlchemyMultiCompanyRepository
from src.application.company_service import CompanyService
from src.application.company_bootstrap_service import CompanyBootstrapService
from src.application.cross_company_service import CrossCompanyService
from src.domain.company import (
    CompanyLifecycle,
    CompanyType,
    CompanyRole,
    RelationshipType,
    DataShareScope,
)
from src.domain.exceptions import (
    TenantIsolationViolationError,
    CrossCompanyAccessDeniedError,
    InvalidLifecycleTransitionError,
)
from src.api.middleware.company_context import get_company_context, CompanyContext

company_router = APIRouter(prefix="/api/v1/companies", tags=["Multi-Company"])
router = company_router


# Pydantic Schemas
class CreateCompanyRequest(BaseModel):
    name: str
    slug: str
    description: str = ""
    legal_name: str = ""
    company_type: str = "AUTONOMOUS"
    industry: str = "TECHNOLOGY"
    currency: str = "USD"


class LifecycleTransitionRequest(BaseModel):
    target_lifecycle: str
    reason: str = ""


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "VIEWER"


class BootstrapCompanyRequest(BaseModel):
    template_id: Optional[str] = None
    custom_governance: Optional[Dict[str, Any]] = None


class CreateRelationshipRequest(BaseModel):
    target_company_id: str
    relationship_type: str = "PARTNER"


class DataShareRequest(BaseModel):
    target_company_id: str
    purpose: str
    data_scope: str = "READ_ONLY"


class ApproveDataShareRequest(BaseModel):
    governance_approval_id: str


@company_router.get("", response_model=List[Dict[str, Any]])
async def list_companies(session: AsyncSession = Depends(get_db_session)):
    repo = SQLAlchemyMultiCompanyRepository(session)
    service = CompanyService(repo)
    companies = await repo.list_companies()
    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "company_type": c.company_type.value,
            "industry": c.industry,
            "lifecycle": c.lifecycle.value,
            "created_at": c.created_at.isoformat(),
        }
        for c in companies
    ]


@company_router.post("", status_code=status.HTTP_201_CREATED)
async def create_company(
    req: CreateCompanyRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    repo = SQLAlchemyMultiCompanyRepository(session)
    service = CompanyService(repo)
    try:
        c = await service.create_company(
            name=req.name,
            slug=req.slug,
            description=req.description,
            legal_name=req.legal_name,
            company_type=CompanyType(req.company_type.upper()),
            industry=req.industry,
            currency=req.currency,
            owner_id=ctx.user_id,
        )
        await session.commit()
        return {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "lifecycle": c.lifecycle.value,
            "message": "Company created successfully",
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@company_router.get("/{company_id}")
async def get_company_details(
    company_id: str,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    ctx.verify_company_access(company_id, "company_details")
    repo = SQLAlchemyMultiCompanyRepository(session)
    c = await repo.get_company_by_id(company_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Company '{company_id}' not found.")

    profile = await repo.get_company_profile(company_id)
    members = await repo.list_memberships_for_company(company_id)

    return {
        "id": c.id,
        "name": c.name,
        "slug": c.slug,
        "lifecycle": c.lifecycle.value,
        "company_type": c.company_type.value,
        "profile": {
            "operating_hours": profile.operating_hours if profile else "24/7",
            "workforce_config": profile.workforce_config if profile else {},
        },
        "members_count": len(members),
    }


@company_router.post("/{company_id}/lifecycle")
async def transition_company_lifecycle(
    company_id: str,
    req: LifecycleTransitionRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    ctx.verify_company_access(company_id, "company_lifecycle")
    repo = SQLAlchemyMultiCompanyRepository(session)
    service = CompanyService(repo)

    try:
        target_state = CompanyLifecycle(req.target_lifecycle.upper())
        c = await service.transition_company_lifecycle(company_id, target_state, actor_id=ctx.user_id, reason=req.reason)
        await session.commit()
        return {"id": c.id, "lifecycle": c.lifecycle.value, "status": "TRANSITION_SUCCESSFUL"}
    except InvalidLifecycleTransitionError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@company_router.post("/{company_id}/bootstrap")
async def bootstrap_company(
    company_id: str,
    req: BootstrapCompanyRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    ctx.verify_company_access(company_id, "company_bootstrap")
    repo = SQLAlchemyMultiCompanyRepository(session)
    service = CompanyBootstrapService(repo)

    try:
        c = await service.bootstrap_company(company_id, template_id=req.template_id, custom_governance=req.custom_governance)
        await session.commit()
        return {"id": c.id, "lifecycle": c.lifecycle.value, "status": "BOOTSTRAP_COMPLETED"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@company_router.post("/{company_id}/relationships")
async def create_relationship(
    company_id: str,
    req: CreateRelationshipRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    ctx.verify_company_access(company_id, "company_relationship")
    repo = SQLAlchemyMultiCompanyRepository(session)
    cross_svc = CrossCompanyService(repo)

    try:
        rel = await cross_svc.create_relationship(company_id, req.target_company_id, RelationshipType(req.relationship_type.upper()))
        await session.commit()
        return {"relationship_id": rel.id, "status": rel.status}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@company_router.post("/{company_id}/data-share")
async def request_data_share(
    company_id: str,
    req: DataShareRequest,
    session: AsyncSession = Depends(get_db_session),
    ctx: CompanyContext = Depends(get_company_context),
):
    ctx.verify_company_access(company_id, "company_data_share")
    repo = SQLAlchemyMultiCompanyRepository(session)
    cross_svc = CrossCompanyService(repo)

    try:
        share_req = await cross_svc.request_data_share(company_id, req.target_company_id, req.purpose, DataShareScope(req.data_scope.upper()))
        await session.commit()
        return {"share_request_id": share_req.id, "status": share_req.status.value}
    except CrossCompanyAccessDeniedError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
