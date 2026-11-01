"""
Request authentication: who is calling, and which tenant they act in.

Credentials are a bearer access token (issued by POST /auth/login) or the ADMIN_API_KEY
sent as X-API-Key. The tenant comes from the credential, never from a client-chosen header;
only platform admins may select another tenant with X-Tenant-ID.
"""

import hmac
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from src.infrastructure.config import settings
from src.infrastructure.security.tokens import InvalidTokenError, decode_access_token

ADMIN_API_KEY_USER_ID = "admin-api-key"


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str | None
    is_platform_admin: bool = False
    email: str | None = None


class AuthenticationFailed(Exception):
    """Credentials were presented but are not valid."""


def principal_from_credentials(bearer_token: str | None, api_key: str | None) -> Principal | None:
    """Return the caller's Principal, None when no credentials were sent."""
    if api_key:
        if settings.ADMIN_API_KEY and hmac.compare_digest(api_key, settings.ADMIN_API_KEY):
            return Principal(user_id=ADMIN_API_KEY_USER_ID, tenant_id=None, is_platform_admin=True)
        raise AuthenticationFailed("Invalid API key.")
    if bearer_token:
        try:
            claims = decode_access_token(bearer_token)
        except InvalidTokenError as exc:
            raise AuthenticationFailed(f"Invalid access token: {exc}") from exc
        return Principal(
            user_id=str(claims["sub"]),
            tenant_id=claims.get("tid"),
            is_platform_admin=bool(claims.get("adm", False)),
            email=claims.get("email"),
        )
    return None


def bearer_token_from_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else None


def get_principal(request: Request) -> Principal | None:
    """FastAPI dependency: the authenticated caller (None only when AUTH_REQUIRED is off)."""
    return getattr(request.state, "principal", None)


def require_platform_admin(request: Request) -> Principal | None:
    principal = get_principal(request)
    if principal is None and not settings.AUTH_REQUIRED:
        return None
    if principal is None or not principal.is_platform_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Platform administrator access required.")
    return principal


def ensure_tenant_access(principal: Principal | None, tenant_id: str | None) -> None:
    """Reject access to another tenant's resource."""
    if principal is None and not settings.AUTH_REQUIRED:
        return
    if principal is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required.")
    if principal.is_platform_admin:
        return
    if tenant_id is None or tenant_id != principal.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This resource belongs to another tenant.")
