"""
Integration tests for Phase 29 Enterprise OS Governance, Policy Inheritance & Inter-Company Authorization.
"""

from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.domain.enterprise import (
    InterCompanyRequest,
    InterCompanyRequestStatus,
    EnterprisePolicyProfile,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_effective_policy_resolution_route(client):
    """
    Verifies that resolve_effective_policy endpoint resolves child policy without weakening root cap.
    """
    with patch("src.api.routes.enterprise.SQLAlchemyEnterpriseRepository") as mock_repo_cls:
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        root_policy = EnterprisePolicyProfile(
            enterprise_id="ent-root-11",
            node_id="ent-root-11",
            max_single_budget_spend_usd=50000.0,
        )
        child_policy = EnterprisePolicyProfile(
            enterprise_id="ent-root-11",
            node_id="node-child-22",
            max_single_budget_spend_usd=150000.0,
        )

        def get_policy(node_id: str):
            if node_id == "ent-root-11":
                return root_policy
            elif node_id == "node-child-22":
                return child_policy
            return None

        mock_repo.get_policy_profile_by_node_id.side_effect = get_policy

        resp = client.get("/api/v1/enterprises/ent-root-11/nodes/node-child-22/effective-policy")
        assert resp.status_code == 200
        data = resp.json()
        assert data["effective_max_single_budget_spend_usd"] == 50000.0


def test_intercompany_request_authorization_bridge(client):
    """
    Verifies that inter-company requests require explicit governance approval prior to authorization.
    """
    with patch("src.api.routes.enterprise.SQLAlchemyEnterpriseRepository") as mock_repo_cls:
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo

        ic_req = InterCompanyRequest(
            id="icreq-7788",
            enterprise_id="ent-root-11",
            source_company_id="comp-a",
            destination_company_id="comp-b",
            requester_id="user-123",
            requested_capability="GPU_SWARM",
            purpose="Testing",
            status=InterCompanyRequestStatus.PENDING,
        )
        mock_repo.get_intercompany_request_by_id.return_value = ic_req
        mock_repo.save_intercompany_request.side_effect = lambda r: r

        resp = client.post(
            "/api/v1/enterprises/ent-root-11/intercompany-requests/icreq-7788/authorize",
            json={"governance_approval_id": "gov-appr-phase29-100"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "AUTHORIZED"
        assert data["governance_approval_id"] == "gov-appr-phase29-100"
