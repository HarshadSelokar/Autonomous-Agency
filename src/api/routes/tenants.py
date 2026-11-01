"""
FastAPI REST Routes for Multi-Tenant Management (Phase 32).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import Principal, ensure_tenant_access, get_principal, require_platform_admin
from src.api.schemas.tenant import (
    TenantCreateSchema,
    TenantResponseSchema,
    TenantUpdateSchema,
    TenantConfigurationSchema,
)
from src.application.tenant_service import TenantService
from src.domain.exceptions import TenantNotFoundError, DuplicateTenantError, InvalidStateTransitionError
from src.domain.tenant import Tenant
from src.infrastructure.database import get_db
from src.infrastructure.repositories.tenant_repository import SQLAlchemyTenantRepository

router = APIRouter(prefix="/tenants", tags=["Multi-Tenancy"])


def get_tenant_service(db: AsyncSession = Depends(get_db)) -> TenantService:
    repo = SQLAlchemyTenantRepository(db)
    return TenantService(tenant_repo=repo)


def _to_response(tenant: Tenant) -> TenantResponseSchema:
    return TenantResponseSchema(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status.value,
        plan=tenant.plan.value,
        configuration=TenantConfigurationSchema(
            max_users=tenant.configuration.max_users,
            max_projects=tenant.configuration.max_projects,
            max_workflows=tenant.configuration.max_workflows,
            allowed_providers=tenant.configuration.allowed_providers,
            custom_settings=tenant.configuration.custom_settings,
        ),
        created_at=str(tenant.created_at),
        updated_at=str(tenant.updated_at),
    )


@router.post("", response_model=TenantResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreateSchema,
    service: TenantService = Depends(get_tenant_service),
    db: AsyncSession = Depends(get_db),
    _admin: Principal | None = Depends(require_platform_admin),
) -> TenantResponseSchema:
    try:
        config_dict = payload.configuration.model_dump() if payload.configuration else None
        tenant = await service.create_tenant(
            name=payload.name,
            slug=payload.slug,
            plan=payload.plan,
            configuration=config_dict,
            tenant_id=payload.tenant_id,
        )
        await db.commit()
        return _to_response(tenant)
    except DuplicateTenantError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/{tenant_id}", response_model=TenantResponseSchema)
async def get_tenant(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
    principal: Principal | None = Depends(get_principal),
) -> TenantResponseSchema:
    ensure_tenant_access(principal, tenant_id)
    try:
        tenant = await service.get_tenant(tenant_id)
        return _to_response(tenant)
    except TenantNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.get("", response_model=List[TenantResponseSchema])
async def list_tenants(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: TenantService = Depends(get_tenant_service),
    _admin: Principal | None = Depends(require_platform_admin),
) -> List[TenantResponseSchema]:
    tenants = await service.list_tenants(limit=limit, offset=offset)
    return [_to_response(t) for t in tenants]


@router.patch("/{tenant_id}", response_model=TenantResponseSchema)
async def update_tenant(
    tenant_id: str,
    payload: TenantUpdateSchema,
    service: TenantService = Depends(get_tenant_service),
    db: AsyncSession = Depends(get_db),
    _admin: Principal | None = Depends(require_platform_admin),
) -> TenantResponseSchema:
    try:
        tenant = await service.get_tenant(tenant_id)

        if payload.name:
            tenant.name = payload.name
            await service.tenant_repo.save(tenant)

        if payload.plan:
            tenant = await service.update_tenant_plan(tenant_id, payload.plan)

        if payload.status:
            tenant = await service.transition_tenant_status(tenant_id, payload.status)

        if payload.configuration:
            tenant = await service.update_tenant_configuration(
                tenant_id, payload.configuration.model_dump()
            )

        await db.commit()
        return _to_response(tenant)
    except TenantNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    except InvalidStateTransitionError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    service: TenantService = Depends(get_tenant_service),
    db: AsyncSession = Depends(get_db),
    _admin: Principal | None = Depends(require_platform_admin),
) -> None:
    try:
        await service.delete_tenant(tenant_id)
        await db.commit()
    except TenantNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
