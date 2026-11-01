"""
Centralized RBAC/ABAC Authorization Engine for User and Agent Permissions (Phase 33).
"""

from src.domain.identity import Membership, Role, ROLE_PERMISSIONS, User
from src.domain.exceptions import UnauthorizedApprovalError, SecurityBoundaryViolationError
from src.infrastructure.repositories.identity_repository import (
    SQLAlchemyMembershipRepository,
    SQLAlchemyUserRepository,
)


class AuthorizationService:
    def __init__(
        self,
        user_repo: SQLAlchemyUserRepository | None = None,
        membership_repo: SQLAlchemyMembershipRepository | None = None,
    ) -> None:
        self.user_repo = user_repo
        self.membership_repo = membership_repo

    async def check_permission(
        self,
        tenant_id: str,
        user_id: str,
        required_permission: str,
        organization_id: str | None = None,
    ) -> bool:
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.tenant_id != tenant_id or user.status != "ACTIVE":
            return False

        if user.is_platform_admin:
            return True

        if organization_id:
            membership = await self.membership_repo.get_membership(
                tenant_id=tenant_id, org_id=organization_id, user_id=user_id
            )
            if membership and membership.is_active:
                return membership.has_permission(required_permission)

        # Check all active organization memberships for user
        memberships = await self.membership_repo.list_by_user(user_id)
        for m in memberships:
            if m.tenant_id == tenant_id and m.is_active:
                if m.has_permission(required_permission):
                    return True

        return False

    async def enforce_permission(
        self,
        tenant_id: str,
        user_id: str,
        required_permission: str,
        organization_id: str | None = None,
    ) -> None:
        allowed = await self.check_permission(
            tenant_id=tenant_id,
            user_id=user_id,
            required_permission=required_permission,
            organization_id=organization_id,
        )
        if not allowed:
            raise SecurityBoundaryViolationError(
                actor_id=user_id,
                violation_type="UNAUTHORIZED_ACCESS",
                details=f"User '{user_id}' lacks required permission '{required_permission}' for tenant '{tenant_id}'.",
            )
