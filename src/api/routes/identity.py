"""
FastAPI REST Routes for Identity, Organizations, and Memberships (Phase 33).
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import Principal, ensure_tenant_access, get_principal
from src.application.authorization_service import AuthorizationService
from src.api.schemas.identity import (
    UserCreateSchema,
    UserResponseSchema,
    OrganizationCreateSchema,
    OrganizationResponseSchema,
    MembershipCreateSchema,
    MembershipResponseSchema,
)
from src.domain.identity import User, UserStatus, Organization, OrganizationStatus, Membership, Role
from src.infrastructure.config import settings
from src.infrastructure.database import get_db
from src.infrastructure.repositories.identity_repository import (
    SQLAlchemyUserRepository,
    SQLAlchemyOrganizationRepository,
    SQLAlchemyMembershipRepository,
)
from src.infrastructure.security.passwords import hash_password

router = APIRouter(prefix="/identity", tags=["Identity & Access Control"])


async def _authorize(
    principal: Principal | None,
    db: AsyncSession,
    tenant_id: str,
    permission: str,
) -> None:
    """The caller must belong to the tenant and hold the permission there."""
    ensure_tenant_access(principal, tenant_id)
    if principal is None or principal.is_platform_admin:
        return
    auth_service = AuthorizationService(
        user_repo=SQLAlchemyUserRepository(db),
        membership_repo=SQLAlchemyMembershipRepository(db),
    )
    if not await auth_service.check_permission(tenant_id, principal.user_id, permission):
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing permission '{permission}'.")


@router.post("/users", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateSchema,
    db: AsyncSession = Depends(get_db),
    principal: Principal | None = Depends(get_principal),
) -> UserResponseSchema:
    await _authorize(principal, db, payload.tenant_id, "user:write")
    if payload.is_platform_admin and settings.AUTH_REQUIRED:
        if principal is None or not principal.is_platform_admin:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only a platform administrator can grant that role."
            )

    repo = SQLAlchemyUserRepository(db)
    if await repo.get_by_email(payload.tenant_id, payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with this email already exists.")
    user_id = f"usr-{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        tenant_id=payload.tenant_id,
        email=payload.email,
        full_name=payload.full_name,
        is_platform_admin=payload.is_platform_admin,
        password_hash=hash_password(payload.password) if payload.password else None,
    )
    saved = await repo.save(user)
    await db.commit()
    return UserResponseSchema(
        id=saved.id,
        tenant_id=saved.tenant_id,
        email=saved.email,
        full_name=saved.full_name,
        status=saved.status.value,
        is_platform_admin=saved.is_platform_admin,
        created_at=str(saved.created_at),
        updated_at=str(saved.updated_at),
    )


@router.post("/organizations", response_model=OrganizationResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreateSchema,
    db: AsyncSession = Depends(get_db),
    principal: Principal | None = Depends(get_principal),
) -> OrganizationResponseSchema:
    await _authorize(principal, db, payload.tenant_id, "organization:write")
    repo = SQLAlchemyOrganizationRepository(db)
    org_id = f"org-{uuid.uuid4().hex[:12]}"
    org = Organization(
        id=org_id,
        tenant_id=payload.tenant_id,
        name=payload.name,
        slug=payload.slug,
        metadata_json=payload.metadata,
    )
    saved = await repo.save(org)
    await db.commit()
    return OrganizationResponseSchema(
        id=saved.id,
        tenant_id=saved.tenant_id,
        name=saved.name,
        slug=saved.slug,
        status=saved.status.value,
        metadata=saved.metadata_json,
        created_at=str(saved.created_at),
        updated_at=str(saved.updated_at),
    )


@router.post("/memberships", response_model=MembershipResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_membership(
    payload: MembershipCreateSchema,
    db: AsyncSession = Depends(get_db),
    principal: Principal | None = Depends(get_principal),
) -> MembershipResponseSchema:
    await _authorize(principal, db, payload.tenant_id, "user:write")
    try:
        role = Role(payload.role.upper())
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown role '{payload.role}'.") from exc
    if role == Role.PLATFORM_ADMIN and settings.AUTH_REQUIRED:
        if principal is None or not principal.is_platform_admin:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only a platform administrator can grant that role."
            )
    repo = SQLAlchemyMembershipRepository(db)
    mem_id = f"mem-{uuid.uuid4().hex[:12]}"
    membership = Membership(
        id=mem_id,
        tenant_id=payload.tenant_id,
        organization_id=payload.organization_id,
        user_id=payload.user_id,
        role=role,
    )
    saved = await repo.save(membership)
    await db.commit()
    return MembershipResponseSchema(
        id=saved.id,
        tenant_id=saved.tenant_id,
        organization_id=saved.organization_id,
        user_id=saved.user_id,
        role=saved.role.value,
        is_active=saved.is_active,
        created_at=str(saved.created_at),
    )
