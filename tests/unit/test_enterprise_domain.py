"""
Unit tests for Phase 29 Enterprise OS domain models & core exceptions.
"""

from datetime import datetime, timedelta, timezone, UTC
import pytest

from src.domain.enterprise import (
    Enterprise,
    EnterpriseProfile,
    EnterpriseLifecycle,
    EnterpriseOrganizationNode,
    NodeType,
    EnterpriseRelationship,
    RelationshipType,
    EnterpriseService,
    ServiceType,
    EnterprisePortfolio,
    PortfolioItem,
    PortfolioCategory,
    PortfolioPriority,
    EnterpriseObjective,
    ObjectiveCascade,
    EnterprisePolicyProfile,
    AuthorityGrant,
    EnterpriseResourcePool,
    ResourceAllocation,
    InterCompanyRequest,
    InterCompanyRequestStatus,
    EnterpriseHealthSnapshot,
    EnterpriseRisk,
    EnterpriseOpportunity,
    DataClassification,
)
from src.domain.exceptions import (
    EnterpriseError,
    UnauthorizedEnterpriseActionError,
    InvalidTopologyCycleError,
    CrossEnterpriseAccessError,
    AuthorityExpiredError,
    ResourceAllocationConflictError,
)


def test_enterprise_instantiation():
    ent = Enterprise(name="Global Corp", code="GCORP")
    assert ent.id.startswith("ent-")
    assert ent.status == EnterpriseLifecycle.PROPOSED
    assert ent.profile.operating_currency == "USD"


def test_enterprise_topology_nodes():
    node = EnterpriseOrganizationNode(
        enterprise_id="ent-123",
        name="Company Alpha",
        node_type=NodeType.COMPANY,
        region="NORTH_AMERICA",
        data_classification=DataClassification.CONFIDENTIAL,
    )
    assert node.id.startswith("node-")
    assert node.node_type == NodeType.COMPANY
    assert node.data_classification == DataClassification.CONFIDENTIAL


def test_enterprise_service_agreements():
    svc = EnterpriseService(
        enterprise_id="ent-123",
        owner_node_id="node-hq",
        name="Central AI Platform",
        service_type=ServiceType.AI_PLATFORM,
        capacity_units=500,
        available_units=500,
    )
    assert svc.id.startswith("svc-")
    assert svc.available_units == 500


def test_authority_grant_expiry():
    grant = AuthorityGrant(
        enterprise_id="ent-123",
        grantor_node_id="node-ent",
        grantee_node_id="node-comp-a",
        scope="BUDGET_ALLOCATION",
        action="ALLOCATE",
        max_impact_usd=100000.0,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )
    assert grant.is_revoked is False
    assert grant.expires_at < datetime.now(UTC)


def test_enterprise_exceptions():
    with pytest.raises(UnauthorizedEnterpriseActionError) as exc_info:
        raise UnauthorizedEnterpriseActionError("ent-123", "TRANSFER_FUNDS", "Autonomous transfers prohibited.")
    assert "Unauthorized enterprise action 'TRANSFER_FUNDS'" in str(exc_info.value)

    with pytest.raises(InvalidTopologyCycleError) as exc_info:
        raise InvalidTopologyCycleError("ent-123", "node-a", "node-b")
    assert "creates a cycle" in str(exc_info.value)

    with pytest.raises(ResourceAllocationConflictError) as exc_info:
        raise ResourceAllocationConflictError("pool-123", requested=150.0, available=100.0)
    assert "Requested 150.0 exceeds available 100.0" in str(exc_info.value)
