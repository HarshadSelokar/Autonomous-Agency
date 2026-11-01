"""
Unit tests for Tenant Domain Entity and State Machine (Phase 32).
"""

import pytest
from src.domain.tenant import Tenant, TenantConfiguration, TenantPlan, TenantStatus
from src.domain.exceptions import InvalidStateTransitionError


def test_tenant_creation_defaults():
    tenant = Tenant(
        id="tenant-123",
        name="Acme Corp",
        slug="acme-corp",
    )
    assert tenant.id == "tenant-123"
    assert tenant.name == "Acme Corp"
    assert tenant.slug == "acme-corp"
    assert tenant.status == TenantStatus.ACTIVE
    assert tenant.plan == TenantPlan.FREE
    assert tenant.configuration.max_users == 100
    assert tenant.is_active() is True


def test_tenant_state_transitions():
    tenant = Tenant(id="t-1", name="Test", slug="test")

    # ACTIVE -> SUSPENDED
    tenant.transition_to(TenantStatus.SUSPENDED)
    assert tenant.status == TenantStatus.SUSPENDED
    assert tenant.is_active() is False

    # SUSPENDED -> ACTIVE
    tenant.transition_to(TenantStatus.ACTIVE)
    assert tenant.status == TenantStatus.ACTIVE

    # ACTIVE -> DELETED
    tenant.transition_to(TenantStatus.DELETED)
    assert tenant.status == TenantStatus.DELETED

    # DELETED is terminal -> transition to ACTIVE raises error
    with pytest.raises(InvalidStateTransitionError):
        tenant.transition_to(TenantStatus.ACTIVE)
