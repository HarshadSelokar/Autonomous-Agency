"""
Unit tests for Identity, Organization, Membership domain entities and RBAC (Phase 33).
"""

import pytest
from src.domain.identity import User, Organization, Membership, Role, UserStatus, OrganizationStatus


def test_user_creation_defaults():
    user = User(
        id="usr-123",
        tenant_id="tenant-1",
        email="john@acme.com",
        full_name="John Doe",
    )
    assert user.id == "usr-123"
    assert user.tenant_id == "tenant-1"
    assert user.status == UserStatus.ACTIVE
    assert user.is_platform_admin is False


def test_membership_rbac_permissions():
    membership_emp = Membership(
        id="mem-1",
        tenant_id="tenant-1",
        organization_id="org-1",
        user_id="usr-1",
        role=Role.EMPLOYEE,
    )
    assert membership_emp.has_permission("task:execute") is True
    assert membership_emp.has_permission("tenant:write") is False

    membership_owner = Membership(
        id="mem-2",
        tenant_id="tenant-1",
        organization_id="org-1",
        user_id="usr-2",
        role=Role.TENANT_OWNER,
    )
    assert membership_owner.has_permission("tenant:write") is True
    assert membership_owner.has_permission("workforce:read") is True
