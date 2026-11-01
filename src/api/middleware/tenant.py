"""
Tenant Context propagation and middleware for multi-tenant request isolation (Phase 32).
"""

from contextvars import ContextVar
from typing import Optional
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from src.api.auth import (
    AuthenticationFailed,
    bearer_token_from_header,
    principal_from_credentials,
)
from src.infrastructure.config import settings

# The context variables live with the ORM scoping that reads them; re-exported for callers
from src.infrastructure.tenant_context import (  # noqa: E402, F401
    _current_tenant_id,
    _current_tenant_slug,
    get_current_tenant_id,
    get_current_tenant_slug,
    set_current_tenant_id,
    set_current_tenant_slug,
)


PUBLIC_PATH_PREFIXES = ("/health", "/auth/login", "/docs", "/redoc", "/openapi.json")


def _is_public(path: str) -> bool:
    return any(path == prefix or path.startswith(prefix + "/") for prefix in PUBLIC_PATH_PREFIXES)


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Authenticates the caller and binds the tenant for the request.

    The tenant comes from the caller's credentials. 'X-Tenant-ID' is honoured only for
    platform admins, or when AUTH_REQUIRED is off (local development and tests).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        requested_tenant = request.headers.get("X-Tenant-ID") or request.query_params.get("tenant_id")
        tenant_slug = request.headers.get("X-Tenant-Slug") or request.query_params.get("tenant_slug")
        public = request.method == "OPTIONS" or _is_public(request.url.path)

        try:
            principal = principal_from_credentials(
                bearer_token_from_header(request.headers.get("Authorization")),
                request.headers.get("X-API-Key"),
            )
        except AuthenticationFailed as exc:
            if not public:
                return _error(status.HTTP_401_UNAUTHORIZED, str(exc))
            principal = None

        if principal is None:
            if settings.AUTH_REQUIRED and not public:
                return _error(status.HTTP_401_UNAUTHORIZED, "Authentication required.")
            tenant_id = requested_tenant
        elif principal.is_platform_admin:
            tenant_id = requested_tenant or principal.tenant_id
        else:
            if requested_tenant and requested_tenant != principal.tenant_id:
                return _error(status.HTTP_403_FORBIDDEN, "You cannot act in another tenant.")
            tenant_id = principal.tenant_id

        token_id = _current_tenant_id.set(tenant_id)
        token_slug = _current_tenant_slug.set(tenant_slug)

        request.state.principal = principal
        request.state.tenant_id = tenant_id
        request.state.tenant_slug = tenant_slug

        try:
            response = await call_next(request)
            if tenant_id:
                response.headers["X-Tenant-ID"] = tenant_id
            return response
        finally:
            _current_tenant_id.reset(token_id)
            _current_tenant_slug.reset(token_slug)
