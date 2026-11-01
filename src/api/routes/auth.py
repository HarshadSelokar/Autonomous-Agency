"""
FastAPI routes for authentication: exchange credentials for an access token.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import Principal, get_principal
from src.api.schemas.identity import (
    LoginRequestSchema,
    PrincipalResponseSchema,
    TokenResponseSchema,
)
from src.domain.identity import UserStatus
from src.infrastructure.config import settings
from src.infrastructure.database import get_db
from src.infrastructure.repositories.identity_repository import SQLAlchemyUserRepository
from src.infrastructure.security.passwords import verify_password
from src.infrastructure.security.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

_INVALID = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")


@router.post("/login", response_model=TokenResponseSchema)
async def login(
    payload: LoginRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> TokenResponseSchema:
    repo = SQLAlchemyUserRepository(db)
    if payload.tenant_id:
        user = await repo.get_by_email(payload.tenant_id, payload.email)
        candidates = [user] if user else []
    else:
        candidates = await repo.find_by_email(payload.email)

    # Same response for unknown user and wrong password, so emails cannot be enumerated
    matching = [u for u in candidates if verify_password(payload.password, u.password_hash)]
    if not matching:
        raise _INVALID
    if len(matching) > 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This email exists in several tenants; send tenant_id."
        )
    user = matching[0]
    if user.status != UserStatus.ACTIVE:
        raise _INVALID

    token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        is_platform_admin=user.is_platform_admin,
        email=user.email,
    )
    return TokenResponseSchema(
        access_token=token, expires_in_seconds=settings.AUTH_TOKEN_TTL_MINUTES * 60
    )


@router.get("/me", response_model=PrincipalResponseSchema)
async def me(principal: Principal | None = Depends(get_principal)) -> PrincipalResponseSchema:
    if principal is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated.")
    return PrincipalResponseSchema(
        user_id=principal.user_id,
        tenant_id=principal.tenant_id,
        is_platform_admin=principal.is_platform_admin,
        email=principal.email,
    )
