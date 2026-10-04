"""
Identity, Organization, Membership, and Access Control Domain Entities (Phase 33).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class OrganizationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class Role(str, Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_OWNER = "TENANT_OWNER"
    ORG_ADMIN = "ORG_ADMIN"
    MANAGER = "MANAGER"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    EMPLOYEE = "EMPLOYEE"
    REVIEWER = "REVIEWER"
    OBSERVER = "OBSERVER"
    CLIENT = "CLIENT"


# Predefined Role Permission Matrix
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.PLATFORM_ADMIN: {"*"},
    Role.TENANT_OWNER: {
        "tenant:*",
        "organization:*",
        "user:*",
        "workforce:*",
        "project:*",
        "workflow:*",
        "budget:*",
        "governance:*",
    },
    Role.ORG_ADMIN: {
        "organization:read",
        "organization:write",
        "user:read",
        "user:write",
        "workforce:read",
        "workforce:write",
        "project:*",
        "workflow:*",
    },
    Role.MANAGER: {
        "project:read",
        "project:write",
        "task:*",
        "workflow:read",
        "workflow:write",
        "workforce:read",
        "artifact:*",
    },
    Role.PROJECT_MANAGER: {
        "project:read",
        "project:write",
        "task:*",
        "workflow:read",
        "workflow:write",
        "artifact:*",
    },
    Role.EMPLOYEE: {
        "project:read",
        "task:read",
        "task:execute",
        "artifact:read",
        "artifact:create",
        "tool:execute",
    },
    Role.REVIEWER: {
        "project:read",
        "task:read",
        "artifact:read",
        "governance:approve",
        "verification:review",
    },
    Role.OBSERVER: {
        "project:read",
        "task:read",
        "workflow:read",
        "artifact:read",
    },
    Role.CLIENT: {
        "project:read",
        "task:read",
        "artifact:read",
        "approval:request",
    },
}


@dataclass
class User:
    id: str
    tenant_id: str
    email: str
    full_name: str
    status: UserStatus = UserStatus.ACTIVE
    is_platform_admin: bool = False
    password_hash: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Organization:
    id: str
    tenant_id: str
    name: str
    slug: str
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    metadata_json: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Membership:
    id: str
    tenant_id: str
    organization_id: str
    user_id: str
    role: Role = Role.EMPLOYEE
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def has_permission(self, permission: str) -> bool:
        allowed_perms = ROLE_PERMISSIONS.get(self.role, set())
        if "*" in allowed_perms:
            return True
        if permission in allowed_perms:
            return True
        # Prefix wildcard matching (e.g. project:read matches project:*)
        domain_prefix = permission.split(":")[0] + ":*"
        return domain_prefix in allowed_perms
